import hashlib, hmac, os, time, jwt
from .config import SECRET_KEY
ALGORITHM = "HS256"
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{salt.hex()}:{digest.hex()}"
def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split(":")
        calculated = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000).hex()
        return hmac.compare_digest(calculated, digest)
    except (ValueError, TypeError):
        return False
def make_token(user_id: int, role: str) -> str:
    return jwt.encode({"sub": str(user_id), "role": role, "iat": int(time.time()), "exp": int(time.time()) + 28800}, SECRET_KEY, algorithm=ALGORITHM)
def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
