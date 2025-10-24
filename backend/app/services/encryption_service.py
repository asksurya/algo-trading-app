"""
Encryption service for secure API key storage
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        """Initialize encryption service with master key"""
        self.master_key = self._get_master_key()
        self.cipher = self._create_cipher()
    
    def _get_master_key(self) -> bytes:
        """Get or generate master encryption key"""
        master_key_b64 = os.getenv("ENCRYPTION_MASTER_KEY")
        
        if not master_key_b64:
            # Generate a new key for development
            # In production, this should be set via environment variable
            print("WARNING: ENCRYPTION_MASTER_KEY not set, generating temporary key")
            key = Fernet.generate_key()
            print(f"Generated key (set this in .env): ENCRYPTION_MASTER_KEY={key.decode()}")
            return key
        
        return master_key_b64.encode()
    
    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher from master key"""
        try:
            return Fernet(self.master_key)
        except Exception:
            # If master key is not valid Fernet key, derive one
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'algo-trading-salt',  # In production, use unique salt per installation
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
            return Fernet(key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt an API key
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Base64 encoded encrypted key
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        encrypted = self.cipher.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key
        
        Args:
            encrypted_key: Base64 encoded encrypted key
            
        Returns:
            Plain text API key
        """
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    def verify_encryption(self) -> bool:
        """
        Verify encryption/decryption is working correctly
        
        Returns:
            True if encryption is working
        """
        try:
            test_data = "test_api_key_12345"
            encrypted = self.encrypt_api_key(test_data)
            decrypted = self.decrypt_api_key(encrypted)
            return decrypted == test_data
        except Exception:
            return False
    
    def rotate_key(self, old_encrypted: str, new_master_key: bytes) -> str:
        """
        Re-encrypt data with a new master key
        
        Args:
            old_encrypted: Data encrypted with current key
            new_master_key: New master key to use
            
        Returns:
            Data encrypted with new key
        """
        # Decrypt with current key
        plaintext = self.decrypt_api_key(old_encrypted)
        
        # Create new cipher with new key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'algo-trading-salt',
            iterations=100000,
            backend=default_backend()
        )
        new_key = base64.urlsafe_b64encode(kdf.derive(new_master_key))
        new_cipher = Fernet(new_key)
        
        # Encrypt with new key
        encrypted = new_cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()


# Singleton instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
