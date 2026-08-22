from app.core.redis_client import redis_client

seat_id = 11

key = f"seat_hold:{seat_id}"

print("Value:", redis_client.get(key))
print("TTL:", redis_client.ttl(key))