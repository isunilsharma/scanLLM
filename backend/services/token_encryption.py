from cryptography.fernet import Fernet
import os
import base64
import hashlib
from dotenv import load_dotenv

load_dotenv()

def get_encryption_key():
    key_str = os.getenv('TOKEN_ENCRYPTION_KEY')
    if not key_str:
        raise ValueError("TOKEN_ENCRYPTION_KEY not set")
    key_bytes = hashlib.sha256(key_str.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)

def encrypt_token(token: str) -> str:
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()
