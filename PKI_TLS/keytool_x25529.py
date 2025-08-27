import os
import argparse
from binascii import hexlify, unhexlify

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

def gen_x24(password: str | None = None, name: str = "keyje"):
    private_keyx = x25519.X25519PrivateKey.generate()
    public_keyx = private_keyx.public_key()

    if password:
        encryption = serialization.BestAvailableEncryption(password.encode())
    else:
        encryption = serialization.NoEncryption()

    private_pem = private_keyx.private_bytes(
        encoding= serialization.Encoding.PEM,
        format= serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )

    public_pem = public_keyx.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_file = f"{name}_private.pem"
    pub_file = f"{name}_public.pem"

    with open(priv_file, "wb") as f:
        f.write(private_pem)

    with open(pub_file, "wb") as f:
        f.write(public_pem)

    print(f"Generated X25519 keypair → {priv_file}, {pub_file}")

def load_priv_key(path:str, password: str | None = None) -> x25519.X25519PrivateKey:
    with open(path) as f:
        data = f.read()
        return serialization.load_pem_private_key(data, password=password.encode if password else None)
    
def load_public_key(path:str):
    with open(path) as f:
        data = f.read()
        return serialization.load_der_public_key(data)
    
def derive_shared_key_hex(priv_path: str, peer_pub_path: str, hkdf_salt: bytes | None = None, info: bytes | None = None, length: int = 32, password: str | None = None) -> str:
    """
    Load a private key and a peer public key, compute X25519 shared secret,
    run through HKDF-SHA256 and return hex-encoded symmetric key of requested length.
    """
    priv = load_priv_key(priv_path, password=password)
    peer_pub = load_public_key(peer_pub_path)

    if not isinstance(peer_pub, x25519.X25519PublicKey):
        raise TypeError("peer key is not an X25519 public key")

    shared = priv.exchange(peer_pub)  # raw shared secret bytes

    # Derive symmetric key via HKDF (SHA-256)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=hkdf_salt,
        info=info,
    )
    key = hkdf.derive(shared)  # e.g., 32 bytes for AES-256 or ChaCha20-Poly1305
    return hexlify(key).decode()

def demo_ephemeral():
    """
    Demonstrates ephemeral X25519 exchange:
     - Alice generates ephemeral key
     - Bob generates static key (or ephemeral)
     - Both derive shared secret -> HKDF -> symmetric key
     - Use ChaCha20-Poly1305 to encrypt/decrypt
    """
    # Alice ephemeral
    alice_priv = x25519.X25519PrivateKey.generate()
    alice_pub = alice_priv.public_key()

    # Bob static (in real life Bob might have a long-term static)
    bob_priv = x25519.X25519PrivateKey.generate()
    bob_pub = bob_priv.public_key()

    # Both compute raw shared secret
    alice_shared = alice_priv.exchange(bob_pub)
    bob_shared = bob_priv.exchange(alice_pub)
    assert alice_shared == bob_shared

    # Derive symmetric key with HKDF
    salt = os.urandom(16)
    info = b"handshake-demo-v1"
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info)
    sym_key = hkdf.derive(alice_shared)  # 32 bytes

    print("Derived symmetric key (hex):", hexlify(sym_key).decode())

    # AEAD encrypt with ChaCha20-Poly1305
    aead = ChaCha20Poly1305(sym_key)
    Nonce = os.urandom(12)
    plaintext = b"secret message to Bob"
    aad = b"header-aad"
    ciphertext =aead.encrypt(nonce=Nonce, data=plaintext, associated_data=aad)

    print("Ciphertext (hex):", hexlify(ciphertext).decode())

    # Bob re-derives same sym_key (simulate)
    hkdf_b = HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=info)
    sym_key_b = hkdf_b.derive(bob_shared)
    aead_b = ChaCha20Poly1305(sym_key_b)
    plaintext2 = aead_b.decrypt(nonce=Nonce, data=ciphertext, associated_data=aad)
    print("Decrypted plaintext:", plaintext2.decode())

def main():
    parser = argparse.ArgumentParser(description="X25519 key tooling: gen-x25519, derive-shared, demo-ephemeral")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("gen-x25519", help="Generate X25519 keypair and save PEMs")
    p1.add_argument("--name", default="mykey", help="Base name for PEM files")
    p1.add_argument("--password", help="Optional password to encrypt private key")

    p2 = sub.add_parser("derive-shared", help="Derive shared symmetric key (HKDF) from private key and peer public key")
    p2.add_argument("--priv", required=True, help="Path to my private PEM")
    p2.add_argument("--peer", required=True, help="Path to peer public PEM")
    p2.add_argument("--salt", help="Optional HKDF salt (hex)")
    p2.add_argument("--info", help="Optional HKDF info string")
    p2.add_argument("--length", type=int, default=32, help="Output key length in bytes (default 32)")
    p2.add_argument("--password", help="Password if private key PEM is encrypted")

    p3 = sub.add_parser("demo-ephemeral", help="Run ephemeral X25519 demo and AEAD encrypt/decrypt")

    args = parser.parse_args()
    if args.cmd == "gen-x25519":
        gen_x24(name=args.name, password=args.password)
    elif args.cmd == "derive-shared":
        salt = unhexlify(args.salt) if args.salt else None
        info = args.info.encode() if args.info else None
        khex = derive_shared_key_hex(args.priv, args.peer, hkdf_salt=salt, info=info, length=args.length, password=args.password)
        print("HKDF-derived key (hex):", khex)
    elif args.cmd == "demo-ephemeral":
        demo_ephemeral()


if __name__ == "__main__":
    main()