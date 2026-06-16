import os
import json
import hashlib
import secrets

CONFIG_FILE = ".sharron_config.json"

class Settings:
    def __init__(self):
        self.passphrase_hash = None
        self.salt = None
        self.sync_dir = None
        self.load_or_create_config()

    def load_or_create_config(self):
        """Loads configuration from file or runs onboarding if it doesn't exist."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.passphrase_hash = data.get("passphrase_hash")
                    # Convert hex salt back to bytes for cryptographic operations later
                    self.salt = bytes.fromhex(data.get("salt"))
                    self.sync_dir = data.get("sync_dir")
                    return
            except Exception as e:
                print(f"Error reading config file, restarting onboarding: {e}")

        # If config doesn't exist or is corrupted, trigger onboarding
        self.run_onboarding()

    def run_onboarding(self):
        """Interactive CLI configuration setup on first run."""
        print("\n👋 Welcome to Sharron! Let's set up your local-first sync folder.")
        
        while True:
            passphrase = input("🔒 Enter a secure network passphrase: ").strip()
            if len(passphrase) >= 8:
                break
            print("❌ Passphrase must be at least 8 characters long.")

        default_dir = os.path.abspath(os.path.join(os.path.expanduser("~"), "SharronDrive"))
        user_dir = input(f"📂 Enter local sync folder path [Default: {default_dir}]: ").strip()
        self.sync_dir = user_dir if user_dir else default_dir

        os.makedirs(self.sync_dir, exist_ok=True)

        raw_salt = secrets.token_bytes(16)
        self.salt = raw_salt

        hasher = hashlib.sha256()
        hasher.update(passphrase.encode('utf-8'))
        self.passphrase_hash = hasher.hexdigest()

        config_data = {
            "passphrase_hash": self.passphrase_hash,
            "salt": self.salt.hex(),  # Store as hex string so JSON can handle it
            "sync_dir": self.sync_dir
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        
        print(f"🎉 Configuration saved! Sharron folder is active at: {self.sync_dir}\n")

    def get_raw_passphrase_for_session(self):
        """
        Prompts user for session verification to derive keys.
        The raw passphrase is never saved to disk.
        """
        while True:
            session_pass = input("🔑 Enter your Sharron passphrase to unlock this session: ").strip()
            hasher = hashlib.sha256()
            hasher.update(session_pass.encode('utf-8'))
            if hasher.hexdigest() == self.passphrase_hash:
                return session_pass
            print("❌ Incorrect passphrase. Try again.")
