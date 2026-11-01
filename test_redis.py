
import redis

client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

client.ping()

print("Redis connected successfully!")

client.set("test_key", "CacheRAG is connected")
print(client.get("test_key"))
