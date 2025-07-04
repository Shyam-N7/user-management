from redis_connxn import r

key = "test_rate_limit:127.0.0.1"
r.set(key, 1, ex=600)  # Set with expiry
value = r.get(key)
ttl = r.ttl(key)

print(f"✅ Redis wrote key = {key}")
print(f"   Value: {value}")
print(f"   TTL:   {ttl}")