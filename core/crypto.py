import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class CryptoEngine:
    def __init__(self, passphrase: str):
        """
        Initializes the CryptoEngine using a passphrase.
        """
        self.key = self._derive_key(passphrase)
        self.cipher = Fernet(self.key)

    def _derive_key(self, passphrase: str) -> bytes:
        """
        Derives a deterministic 32-byte key from the passphrase.
        Uses a fixed system salt so the key is uniform across all devices.
        """
        STATIC_SYSTEM_SALT = b'sharron_mesh_fixed_backbone_salt'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=STATIC_SYSTEM_SALT,
            iterations=100000
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode('utf-8')))

    def encrypt_data(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

    def decrypt_data(self, data: bytes) -> bytes:
        return self.cipher.decrypt(data)

    def generate_challenge(self) -> str:
        return base64.b64encode(os.urandom(32)).decode('utf-8')

    def solve_challenge(self) -> str:
        return self.cipher.encrypt(challenge.encode('utf-8')).decode('utf-8')

    def verify_challenge_solution(self, original_challenge: str, solution: str) -> bool:
        try:
            decrypted_solution = self.cipher.decrypt(solution.encode('utf-8')).decode('utf-8')
            return decrypted_solution == original_challenge
        except Exception:
            return False