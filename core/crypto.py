import base64
import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

class CryptoEngine:
    def __init__(self, passphrase: str, salt: bytes):
        """
        Initializes the cryptographic engine using the user's passphrase
        and the unique local salt loaded from settings.
        """
        self.key = self._derive_key(passphrase, salt)
        self.fernet = Fernet(self.key)

    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        """
        Stretches the passphrase into a secure 32-byte key using PBKDF2.
        This ensures the text password safely conforms to AES-256 requirements.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000
        )
        # Derive the key and encode it in URL-safe Base64 as required by Fernet
        derived = kdf.derive(passphrase.encode('utf-8'))
        return base64.urlsafe_b64encode(derived)

    def generate_challenge(self) -> str:
        """Generates a random token (nonce) to be used in the authentication handshake."""
        return secrets.token_hex(16)

    def solve_challenge(self, challenge: str) -> str:
        """
        Signs a challenge string by encrypting it. 
        Only another peer with the exact same passphrase key can decrypt and verify it.
        """
        return self.encrypt_data(challenge.encode('utf-8')).decode('utf-8')

    def verify_challenge_solution(self, original_challenge: str, encrypted_solution: str) -> bool:
        """
        Decrypts a received solution and validates if it matches the original challenge.
        Returns True if authenticated, False if dropped/unauthorized.
        """
        try:
            decrypted = self.decrypt_data(encrypted_solution.encode('utf-8'))
            return decrypted.decode('utf-8') == original_challenge
        except Exception:
            return False

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypts a raw byte array.
        Automatically handles generating an Initialization Vector (IV) and a signature tag.
        """
        return self.fernet.encrypt(data)

    def decrypt_data(self, ciphertext: bytes) -> bytes:
        """
        Decrypts a raw byte array.
        Throws an exception if the data has been altered or tampered with in transit.
        """
        return self.fernet.decrypt(ciphertext)
