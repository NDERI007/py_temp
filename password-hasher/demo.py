import hmac, hashlib

def make_hmac(key_bytes, msg):
    return hmac.new(key_bytes, msg, hashlib.sha256).hexdigest()

key1= b"\x05" # 1 byte key (toy — insecure)
msg= b"cyberinnit"
mac = make_hmac(key1, msg)
print("Given mac:", mac)

# Attacker brute-force key: try all 1-byte keys
for k in range(256):
    cand =bytes([k])
    if make_hmac(cand, msg) == mac:
        print("Found youuu:", cand)
        break