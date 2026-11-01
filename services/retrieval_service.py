
import numpy as np

from services.embedding_service import generate_embeddings


def retrieve_relevant_chunks(question, chunks, chunk_embeddings, top_k=3):

    # STEP 1: Generate embedding for user question
    question_embedding = generate_embeddings([question])[0]

    # STEP 2: Calculate cosine similarity
    question_norm = np.linalg.norm(question_embedding)

    chunk_norms = np.linalg.norm(
        chunk_embeddings,
        axis=1
    )

    similarities = np.dot(
        chunk_embeddings,
        question_embedding
    ) / (chunk_norms * question_norm + 1e-10)

    # STEP 3: Get indices of top matching chunks
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # STEP 4: Prepare results
    results = []

    for index in top_indices:

        results.append({
            "chunk": chunks[index],
            "similarity": float(similarities[index]),
            "index": int(index)
        })

    return results
