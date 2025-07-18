# from passlib.context import CryptContext
# from datetime import datetime, timedelta, timezone
# from jose import jwt
# import os
# from dotenv import load_dotenv

# load_dotenv()

# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# if not SECRET_KEY:
#     raise ValueError("SECRET_KEY environment variable is not set! Please check your .env file.")

# password_content = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash_password(password: str):
#     return password_content.hash(password)

# def verify_password(original_password, hashed_password):
#     return password_content.verify(original_password, hashed_password)

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv
from jwt import PyJWTError
from fastapi import Request, HTTPException
from typing import Optional
from collections import defaultdict
import time
import re
import logging
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

login_attempts = defaultdict(list)
blocked_ips = defaultdict(float)

MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION = 900
ATTEMPT_WINDOW = 300

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set! Please check your .env file.")

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return password_context.hash(password)

def verify_password(original_password, hashed_password):
    return password_context.verify(original_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
        
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
def create_password_reset_token(user_id: int, email: str):
    to_encode = {
        "user_id": user_id,
        "email": email,
        "type": "password_reset"
    }
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        return payload
    except PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name_field(name: str, field_name: str) -> bool:
    if not name or len(name.strip()) == 0:
        return False
    
    if len(name) > 50:  # Reasonable length limit
        return False
    
    # Allow only letters, spaces, hyphens, apostrophes
    pattern = r'^[a-zA-Z\s\-]+$'
    if not re.match(pattern, name):
        return False
    
    return True

def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        return False
    if len(password) > 128:  # Prevent DoS
        return False
    if not re.search(r'[A-Z]', password):  # Uppercase
        return False
    if not re.search(r'[a-z]', password):  # Lowercase
        return False
    if not re.search(r'\d', password):     # Number
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Special char
        return False
    
    return True

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host

def is_rate_limited(ip_address: str) -> tuple[bool, Optional[str]]:
    current_time = time.time()
    
    # Check if IP is currently blocked
    if ip_address in blocked_ips:
        if current_time < blocked_ips[ip_address]:
            remaining_time = int(blocked_ips[ip_address] - current_time)
            return True, f"Too many failed attempts. Try again in {remaining_time} seconds"
        else:
            del blocked_ips[ip_address]
            login_attempts[ip_address] = []
    
    # Clean old attempts
    cutoff_time = current_time - ATTEMPT_WINDOW
    login_attempts[ip_address] = [
        attempt_time for attempt_time in login_attempts[ip_address] 
        if attempt_time > cutoff_time
    ]
    
    # Check if too many attempts
    if len(login_attempts[ip_address]) >= MAX_LOGIN_ATTEMPTS:
        blocked_ips[ip_address] = current_time + BLOCK_DURATION
        logger.warning(f"IP {ip_address} blocked due to too many failed login attempts")
        return True, f"Too many failed attempts. Blocked for {BLOCK_DURATION // 60} minutes"
    
    return False, None

def record_failed_attempt(ip_address: str):
    current_time = time.time()
    login_attempts[ip_address].append(current_time)
    
def sanitize_input(input_string: str) -> str:
    if not input_string:
        return ""
    
    sanitized = input_string.replace('\x00', '').strip()
    return sanitized[:255]

def hash_sensitive_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:8]
    
# FOR CHARAIVETI

def validate_usn_field(usn: str, field_name: str) -> bool:
    if not usn or len(usn.strip()) == 0:
        return False
    
    if len(usn) > 40:
        return False

    pattern = r'^[a-zA-Z0-9]+$'
    return re.match(pattern, usn) is not None

def sanitize_usn(input_string: str) -> str:
    if not input_string:
        return ""
    
    sanitized = re.sub(r'[^a-zA-Z0-9]', '', input_string)
    return sanitized