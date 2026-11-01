
import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)


def generate_answer(question, retrieved_chunks):

    context = "\n\n".join(
        result["chunk"] for result in retrieved_chunks
    )

    system_prompt = """
    You are CacheRAG, a document question-answering assistant.

    Answer using ONLY the provided document context.

    Rules:
    1. Give accurate and clear answers.
    2. Do not invent facts.
    3. If the context does not contain the answer,
       clearly say that the document does not provide enough information.
    4. Keep answers concise and informative.
    """

    user_prompt = f"""
    Document Context:
    {context}

    User Question:
    {question}

    Answer based on the provided context.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        max_completion_tokens=1000
    )

    return response.choices[0].message.content