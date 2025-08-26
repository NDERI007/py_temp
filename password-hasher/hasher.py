"""
Demo-only password hashing using SHA-256.
⚠️ Educational, not for production.

Problems:
- It's FAST -> attackers can brute-force billions of guesses/second on GPUs.
- No work factor (not tunable) -> can't slow attackers down.
Use bcrypt/argon2 instead (see secure_hasher.py).
"""
from __future__ import annotations
import os #used to generate random bytes for the salt
import hashlib #provides cryptographic hash functions (SHA-256, etc).
import hmac #gives tools for secure comparisons (constant-time comparison to avoid timing attacks).

ALG = "sha256"
SALT_LEN = 16 # 128-bit salt Salts prevent attacks like precomputed rainbow tables because each password will hash differently even if the password itself is the same.

def _b2h(b: bytes) -> str:
    return b.hex()

def _h2b(s:str) -> bytes:
    return bytes.fromhex(s)

def hash_password_sha(password:str) -> str:
    """
    Returns a self-contained string: "sha256$<salt_hex>$<hash_hex>"
    """
    if not isinstance(password, str):
        raise TypeError("password must be string")
    
    salt = os.urandom(SALT_LEN)  # random per-password salt
    digest = hashlib.sha256(salt + password.encode("UTF-8")).digest() #Concatenates the salt and password, hashes them with SHA-256.
    return f"{ALG}${_b2h(salt)}${_b2h(digest)}"

def verify_password_sha256(password: str, stored: str) -> bool:
    """
    Recomputes the hash from the stored salt and compares in constant-time.
    """
    try:
        alg, salt_hex, hash_hex = stored.split("$", 2)
    except ValueError:
        raise ValueError("stored hash has invalid format")

    if alg != ALG:
        raise ValueError(f"unsupported algorithm tag: {alg}")

    salt = _h2b(salt_hex)
    expected = _h2b(hash_hex)
    actual = hashlib.sha256(salt + password.encode("utf-8")).digest()

    # constant-time comparison to reduce timing side channels
    return hmac.compare_digest(actual, expected)
