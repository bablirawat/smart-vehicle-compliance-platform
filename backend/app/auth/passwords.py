import hashlib
import hmac

def get_password_hash(password: str) -> str:
    # Use standard PBKDF2 HMAC SHA256 for fast, zero-warning password hashing
    salt = "smart_vehicle_salt_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    return hmac.compare_digest(get_password_hash(plain_password), hashed_password)
