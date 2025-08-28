# Project Name

# 🔐 Ed25519 vs X25519 — Curve25519 Use Cases

Curve25519 is one of the most widely used elliptic curves in modern cryptography.  
Two popular algorithms are built on it: **Ed25519 (signatures)** and **X25519 (key exchange)**.  
They look similar but solve very different problems.

---

## ✍️ Ed25519 — Digital Signatures

**Ed25519** is an implementation of EdDSA (Edwards-curve Digital Signature Algorithm) on Curve25519.

✅ **What it does:** Proves that a message came from you (authentication) and wasn’t modified (integrity).  
❌ **What it doesn’t do:** Encryption or key exchange.

🔑 **Key type:** Static (long-lived) identity keys.

📌 **Common uses:**

- SSH host keys
- Signing software updates
- Digital certificates
- Message integrity checks

**Example:**

```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate signing key
priv = ed25519.Ed25519PrivateKey.generate()
pub = priv.public_key()

# Sign and verify
msg = b"important data"
sig = priv.sign(msg)
pub.verify(sig, msg)  # ✅ raises no exception if valid
```

## 🔑 X25519 — Key Exchange

**X25519** is an implementation of Diffie–Hellman key exchange using Curve25519.

✅ **What it does:** Lets two parties who have never met derive the same shared secret over an insecure channel.  
❌ **What it doesn’t do:** Prove who you’re talking to (no authentication).

🔑 **Key type:** Usually ephemeral (temporary, per-session), but can also be static for servers.

📌 **Common uses:**

- TLS 1.3 key exchange
- Signal / WhatsApp end-to-end encryption
- VPN protocols (WireGuard, Noise framework)
- Encrypted messaging apps

**Example:**

```python
from cryptography.hazmat.primitives.asymmetric import x25519

# Alice and Bob generate private keys
alice_priv = x25519.X25519PrivateKey.generate()
bob_priv = x25519.X25519PrivateKey.generate()

# Exchange public keys and derive shared secret
shared_a = alice_priv.exchange(bob_priv.public_key())
shared_b = bob_priv.exchange(alice_priv.public_key())

assert shared_a == shared_b  # ✅ both sides match
```
