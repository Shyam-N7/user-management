from fastapi import HTTPException
import redis

# Constants for different endpoints
CLIENT_LOGIN_PREFIX = "client_login_attempts:"
STUDENT_LOGIN_PREFIX = "student_login_attempts:"
FACULTY_LOGIN_PREFIX = "faculty_login_attempts:"
FORGOT_PASSWORD_PREFIX = "forgot_password_attempts:"


BLOCK_TIME_SECONDS = 600  # 10 minutes
MAX_ATTEMPTS = 5

FORGOT_PASSWORD_MAX_ATTEMPTS = 3
FORGOT_PASSWORD_BLOCK_TIME = 900

def check_rate_limit(client_ip: str, redis_client: redis.Redis, endpoint_prefix: str = CLIENT_LOGIN_PREFIX):
    key = f"{endpoint_prefix}{client_ip}"
    attempts = redis_client.get(key)
    print(f"[check_rate_limit] {key} = {attempts}")
    
    if attempts:
        attempts = int(attempts)
        if attempts >= MAX_ATTEMPTS:
            ttl = redis_client.ttl(key)
            print(f"[RateLimit] BLOCKED {client_ip} for {ttl} seconds")
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many login attempts. "
                    f"Try again in {ttl} seconds. "
                    f"You used {attempts} of {MAX_ATTEMPTS} attempts."
                )
            )

def record_failed_attempt_redis(client_ip: str, redis_client: redis.Redis, endpoint_prefix: str = CLIENT_LOGIN_PREFIX):
    key = f"{endpoint_prefix}{client_ip}"
    print(f"[record_failed_attempt] Incrementing {key}")
    
    try:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, BLOCK_TIME_SECONDS)
        pipe.execute()
        current_attempts = redis_client.get(key)
        print(f"[record_failed_attempt] Current value: {current_attempts}")
        
        # Check if we've hit the limit and warn
        if current_attempts and int(current_attempts) >= MAX_ATTEMPTS:
            print(f"[record_failed_attempt] IP {client_ip} has reached max attempts ({MAX_ATTEMPTS})")
            
    except Exception as e:
        print(f"[record_failed_attempt] Error: {e}")
        raise
    
def reset_failed_attempts(client_ip: str, redis_client: redis.Redis, endpoint_prefix: str = CLIENT_LOGIN_PREFIX):
    key = f"{endpoint_prefix}{client_ip}"
    deleted = redis_client.delete(key)
    print(f"[reset_failed_attempts] Deleted {key}, result: {deleted}")
    
def get_remaining_attempts(client_ip: str, redis_client: redis.Redis, endpoint_prefix: str = CLIENT_LOGIN_PREFIX):
    key = f"{endpoint_prefix}{client_ip}"
    attempts = redis_client.get(key)
    attempts = int(attempts) if attempts else 0
    remaining = max(0, MAX_ATTEMPTS - attempts)
    print(f"[get_remaining_attempts] IP {client_ip}: {attempts} attempts used, {remaining} remaining")
    return remaining

def get_rate_limit_info(client_ip: str, redis_client: redis.Redis, endpoint_prefix: str = CLIENT_LOGIN_PREFIX):
    key = f"{endpoint_prefix}{client_ip}"
    attempts = redis_client.get(key)
    attempts = int(attempts) if attempts else 0
    ttl = redis_client.ttl(key) if attempts > 0 else -1
    remaining = max(0, MAX_ATTEMPTS - attempts)
    
    return {
        "ip": client_ip,
        "attempts": attempts,
        "max_attempts": MAX_ATTEMPTS,
        "remaining": remaining,
        "ttl": ttl,
        "blocked": attempts >= MAX_ATTEMPTS,
        "endpoint": endpoint_prefix.rstrip(':')
    }

# Convenience functions for specific endpoints
def check_client_rate_limit(client_ip: str, redis_client: redis.Redis):
    return check_rate_limit(client_ip, redis_client, CLIENT_LOGIN_PREFIX)

def check_student_rate_limit(client_ip: str, redis_client: redis.Redis):
    return check_rate_limit(client_ip, redis_client, STUDENT_LOGIN_PREFIX)

def record_client_failed_attempt(client_ip: str, redis_client: redis.Redis):
    return record_failed_attempt_redis(client_ip, redis_client, CLIENT_LOGIN_PREFIX)

def record_student_failed_attempt(client_ip: str, redis_client: redis.Redis):
    return record_failed_attempt_redis(client_ip, redis_client, STUDENT_LOGIN_PREFIX)

def get_client_remaining_attempts(client_ip: str, redis_client: redis.Redis):
    return get_remaining_attempts(client_ip, redis_client, CLIENT_LOGIN_PREFIX)

def get_student_remaining_attempts(client_ip: str, redis_client: redis.Redis):
    return get_remaining_attempts(client_ip, redis_client, STUDENT_LOGIN_PREFIX)

def check_faculty_rate_limit(client_ip: str, redis_client: redis.Redis):
    return check_rate_limit(client_ip, redis_client, FACULTY_LOGIN_PREFIX)

def record_faculty_failed_attempt(client_ip: str, redis_client: redis.Redis):
    return record_failed_attempt_redis(client_ip, redis_client, FACULTY_LOGIN_PREFIX)

def get_faculty_remaining_attempts(client_ip: str, redis_client: redis.Redis):
    return get_remaining_attempts(client_ip, redis_client, FACULTY_LOGIN_PREFIX)

def check_forgot_password_rate_limit(client_ip: str, redis_client: redis.Redis):
    key = f"{FORGOT_PASSWORD_PREFIX}{client_ip}"
    attempts = redis_client.get(key)
    
    if attempts:
        attempts = int(attempts)
        if attempts >= FORGOT_PASSWORD_MAX_ATTEMPTS:
            ttl = redis_client.ttl(key)
            raise HTTPException(
                status_code=429,
                detail=f"Too many password reset attempts. Try again in {ttl} seconds."
            )

def record_forgot_password_failed_attempt(client_ip: str, redis_client: redis.Redis):
    return record_failed_attempt_redis(client_ip, redis_client, FORGOT_PASSWORD_PREFIX)

def get_forgot_password_remaining_attempts(client_ip: str, redis_client: redis.Redis):
    return get_remaining_attempts(client_ip, redis_client, FORGOT_PASSWORD_PREFIX)

def reset_forgot_password_attempts(client_ip: str, redis_client: redis.Redis):
    key = f"{FORGOT_PASSWORD_PREFIX}{client_ip}"
    deleted = redis_client.delete(key)
    print(f"[reset_failed_attempts] Deleted {key}, result: {deleted}")