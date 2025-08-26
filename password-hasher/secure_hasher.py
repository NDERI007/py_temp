"""
Production-ready password hashing using bcrypt.

- Slow & tunable (work factor / cost).
- Salt is generated and embedded automatically.
- Stored value is a self-contained string (UTF-8).
"""

from __future__ import annotations
import bcrypt

def hash_password(password: str, cost: int | None = None) -> str:
    """
    Returns a bcrypt hash string (e.g., "$2b$12$..."), UTF-8 decoded.
    `cost` (aka rounds) defaults to library default (~12). Higher = slower & safer.
    """
    if not isinstance(password, str):
        raise TypeError("password must be str")

    if cost is None:
        salt = bcrypt.gensalt()                # default cost
    else:
        salt = bcrypt.gensalt(rounds=cost)     # explicit cost

    hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, stored: str) -> bool:
    """
    Verifies a bcrypt-stored hash string.
    """
    if not isinstance(stored, str):
        raise TypeError("stored must be str")
    return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
