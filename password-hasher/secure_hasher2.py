import os
from argon2 import PasswordHasher

ph = PasswordHasher()

PEPPER= os.getenv("APP_PEPER", "G2KNW")

def hash_password(password:str) -> str:
    """
    Hash a password with Argon2 + pepper.
    Argon2 automatically handles the salt.
    """
    # Add pepper before hashing
    password_with_pepper = password + PEPPER
    return ph.hash(password_with_pepper)

def verify_password(password:str, stored_hash: str) -> bool:
     """
    Verify a password against a stored Argon2 hash.
    """
     try:
          password_with_pepper = password + PEPPER
          return ph.verify(stored_hash, password_with_pepper)
     except Exception:
          return False
