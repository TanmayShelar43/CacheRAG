
import redis
import numpy as np

client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=False
)

# Sample 4-dimensional vector
vector = np.array(
    [0.1, 0.2, 0.3, 0.4],
    dtype=np.float32
)

vector_bytes = vector.tobytes()

# Store vector
result = client.execute_command(
    "VADD",
    "test_vectors",
    "FP32",
    vector_bytes,
    "item_1"
)

print("VADD result:", result)

# Search for a similar vector
query_vector = np.array(
    [0.1, 0.2, 0.3, 0.4],
    dtype=np.float32
)

query_bytes = query_vector.tobytes()

result = client.execute_command(
    "VSIM",
    "test_vectors",
    "FP32",
    query_bytes,
    "COUNT",
    3
)

print("VSIM result:", result)
