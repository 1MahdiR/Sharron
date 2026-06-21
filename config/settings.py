import os
import json

CONFIG_FILE = ".sharron_config.json"

class Settings:
    def __init__(self):
        self.sync_path = ""
        self.passphrase_cache = ""
        self.load_settings()

    def is_onboarded(self) -> bool:
        return os.path.exists(CONFIG_FILE) and self.sync_path != ""

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.sync_path = data.get("sync_path", "")
            except Exception:
                pass

    def initialize_fresh_cluster(self, default_path="SharronDrive"):
        self.sync_path = os.path.abspath(default_path)
        if not os.path.exists(self.sync_path):
            os.makedirs(self.sync_path)
        
        config_data = {
            "sync_path": self.sync_path
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)

    def save_passphrase_to_memory(self, passphrase: str):
        self.passphrase_cache = passphrase

    def get_raw_passphrase_for_session(self) -> str:
        if not self.passphrase_cache:
            self.passphrase_cache = input("🔑 Enter your Sharron passphrase to unlock this session: ")
        return self.passphrase_cache