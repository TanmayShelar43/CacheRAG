
from services.cache_service import store_cache, search_cache

# Original question
original_question = "What is semantic chunking?"

answer = (
    "Semantic chunking divides documents into meaningful "
    "sections based on the semantic similarity of sentences."
)

# Store original question and answer
store_cache(original_question, answer)

# Ask the same thing using different wording
new_question = "How are documents divided based on their meaning?"

print("\nNew Question:", new_question)

# Search Redis cache
result = search_cache(new_question)

if result:
    print("\nCACHE HIT!")
    print("Matched Question:", result["question"])
    print("Cached Answer:", result["answer"])
    print("Similarity:", result["similarity"])
else:
    print("\nCACHE MISS!")
    print("No sufficiently similar question found.")
