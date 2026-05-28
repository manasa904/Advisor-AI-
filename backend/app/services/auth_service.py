import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

SECRET_KEY = "advisorai-secret-key-2024-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

USERS_DB = {
    "advisor1":    {"username":"advisor1",    "full_name":"Rajesh Kumar",  "role":"ADVISOR",     "rm_id":"RM001", "hashed_password": hash_password("advisor123"),    "disabled":False},
    "advisor2":    {"username":"advisor2",    "full_name":"Priya Singh",   "role":"ADVISOR",     "rm_id":"RM002", "hashed_password": hash_password("advisor123"),    "disabled":False},
    "compliance1": {"username":"compliance1", "full_name":"Amit Sharma",   "role":"COMPLIANCE",  "rm_id":None,    "hashed_password": hash_password("compliance123"), "disabled":False},
    "ops1":        {"username":"ops1",        "full_name":"Sunita Patel",  "role":"OPERATIONS",  "rm_id":None,    "hashed_password": hash_password("ops123"),        "disabled":False},
}

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = USERS_DB.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None