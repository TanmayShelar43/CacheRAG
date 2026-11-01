
import redis
import numpy as np

from services.embedding_service import generate_embeddings


# Redis connection
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=False
)

CACHE_INDEX = "cache:semantic"

SIMILARITY_THRESHOLD = 0.75


def store_cache(question, answer):

    # Generate question embedding
    embedding = generate_embeddings([question])[0]

    # Convert embedding to FP32 binary
    embedding_bytes = np.asarray(
        embedding,
        dtype=np.float32
    ).tobytes()

    # Generate unique cache ID
    cache_id = f"cache:{redis_client.incr('cache:id')}"

    # Store vector in Redis Vector Set
    redis_client.execute_command(
        "VADD",
        CACHE_INDEX,
        "FP32",
        embedding_bytes,
        cache_id
    )

    # Store question and answer
    redis_client.hset(
        cache_id,
        mapping={
            "question": question.encode("utf-8"),
            "answer": answer.encode("utf-8")
        }
    )

    print("Cache entry stored:", cache_id)

    return cache_id


def search_cache(question):

    # Generate question embedding
    embedding = generate_embeddings([question])[0]

    # Convert to FP32 binary
    embedding_bytes = np.asarray(
        embedding,
        dtype=np.float32
    ).tobytes()

    # Search for similar vectors
    results = redis_client.execute_command(
        "VSIM",
        CACHE_INDEX,
        "FP32",
        embedding_bytes,
        "COUNT",
        1,
        "WITHSCORES"
    )

    if not results:
        return None

    # VSIM returns a dictionary: {ID: similarity_score}
    cache_id, similarity = next(iter(results.items()))

    cache_id = cache_id.decode("utf-8")
    similarity = float(similarity)

    print("Matched Cache ID:", cache_id)
    print("Similarity Score:", similarity)

    # Check similarity threshold
    if similarity < SIMILARITY_THRESHOLD:
        return None

    # Fetch cached question and answer
    cached_data = redis_client.hgetall(cache_id)

    if not cached_data:
        return None

    return {
        "question": cached_data[b"question"].decode("utf-8"),
        "answer": cached_data[b"answer"].decode("utf-8"),
        "similarity": similarity
    }


def clear_cache():

    # Delete the Redis Vector Set
    redis_client.delete(CACHE_INDEX)

    # Delete all cached question-answer hashes
    keys = list(
        redis_client.scan_iter(match=b"cache:[0-9]*")
    )

    if keys:
        redis_client.delete(*keys)

    print("Semantic cache cleared successfully!")