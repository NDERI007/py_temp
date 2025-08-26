from hasher import hash_password_sha, verify_password_sha256
from secure_hasher import hash_password, verify_password

def test_sha256_roundtrip_and_format():
    pw = "test123!"
    stored = hash_password_sha(pw)
    # format: sha256$<salt>$<hash>
    assert stored.startswith("sha256$")
    assert verify_password_sha256(pw, stored)
    assert not verify_password_sha256("wrong", stored)

def test_sha256_salt_makes_hash_unique():
    pw="same-password"
    a= hash_password_sha(pw)
    b = hash_password_sha(pw)
    assert a != b

def test_bcrypt_roundtrip():
    pw = "S0mething#Strong"
    stored = hash_password(pw)
    assert stored.startswith("$2")   # bcrypt signature
    assert verify_password(pw, stored)
    assert not verify_password("wrong", stored)

def test_bcrypt_random_salt_each_time():
    pw = "same-password"
    a = hash_password(pw)
    b = hash_password(pw)
    assert a != b  # bcrypt embeds a random salt -> unique per call