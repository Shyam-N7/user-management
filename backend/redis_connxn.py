import os
import redis
from dotenv import load_dotenv

load_dotenv()

# Your Upstash URL (stored in .env)
REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("REDIS_URL is not set in .env")

# Connect to Upstash
r = redis.from_url(REDIS_URL, decode_responses=True)

# Test connection
print("Connected:", r.ping())