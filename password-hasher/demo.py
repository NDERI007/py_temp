from hasher import hash_password_sha, verify_password_sha256
from secure_hasher import hash_password, verify_password

pd = "fireForcec8"

def main():
    pd="fireForcec8"
    print("=== BAD: SHA-256 ===")
    stored_weak= hash_password_sha(pd)
    print("Stored")
    print("ok", verify_password_sha256(pd, stored_weak))
    print("Wrong", verify_password_sha256("oops", stored_weak))

    print("\n=== GOOD: bcrypt ===")
    stored_strong= hash_password(pd) #default cost
    print("stored")
    print("Ok",  verify_password(pd, stored_strong))
    print("Wrong", verify_password("oops", stored_strong))

if __name__ == "__main__":
    main()