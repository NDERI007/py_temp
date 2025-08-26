# 🔐 Password Security Playground

A hands-on project exploring **cryptography fundamentals**, password hashing, and secure design choices.  
The goal is to contrast **unsafe** practices with **modern secure** ones, and document the trade-offs.

---

## 📖 What I Learned

### 1. Where SHA-256 shines

- ✅ Great for **integrity checks**: detecting corruption/tampering in files (`sha256sum ubuntu.iso`).
- ✅ Used in **Git commits** and **deduplication** (Dropbox used it to detect duplicate file chunks).
- ✅ **Fast** → computers can hash gigabytes quickly.

⚠️ **Bad for password storage**:

- Too fast → attackers can brute-force billions of guesses per second with GPUs/ASICs.
- No built-in salt → vulnerable to rainbow tables unless you add one manually.

---

### 2. Bcrypt

- ✅ Slows down brute force by being **intentionally computationally expensive**.
- ✅ Has a built-in **salt** to prevent rainbow table attacks.
- ⚠️ Weaknesses:
  - Old design (from 1999).
  - Limited to **72 bytes max password length**.
  - No native memory-hardness → GPUs/ASICs can still attack bcrypt efficiently cause bcrypt is cpu bound.

---

### 3. Argon2 (modern winner)

- ✅ Supports **memory-hardness** → makes GPU/ASIC attacks very costly.
- ✅ Built-in salt.
- ✅ Configurable cost factors:
  - `time_cost`: how many iterations.
  - `memory_cost`: how much RAM to use.
  - `parallelism`: number of threads.

⚠️ Weaknesses:

- More complex to configure → if misconfigured, can be too weak.
- Uses more resources → not ideal for ultra-low-power devices.

---

### 4. Salt vs Pepper

- **Salt**: random value stored alongside hash, protects against rainbow tables.
- **Pepper**: secret value stored separately (e.g., in environment variable / key vault).
  - Adds extra protection if DB is leaked.
  - ⚠️ If pepper is weak or exposed, security benefit is lost.

---

## 🛠️ Current Implementation

- **Hashing**: Argon2id via [`argon2-cffi`]
- **Verification**: Argon2id with appended **pepper**
- **Unit tests**:
  - ✅ Verify correct password passes
  - ✅ Verify wrong password fails
  - ✅ Changing pepper invalidates old hashes

---

## 🚫 Unsafe Example

```python
import hashlib

def bad_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
```
