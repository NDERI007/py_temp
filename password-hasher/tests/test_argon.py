from secure_hasher2 import hash_password, verify_password

def test_Argone():
    pw = "test123!"
    
    stored = hash_password(pw)
    assert verify_password(pw, stored)
    assert not verify_password("wrong", stored)

def test_hashes_are_different_each_time():
    password = "supersecret123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2  # Argon2 uses random salt
