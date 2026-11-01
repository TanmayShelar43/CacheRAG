
from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


def create_semantic_chunks(text):

    # Load local embedding model
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Configure semantic splitter
    splitter = SemanticSplitterNodeParser.from_defaults(
        embed_model=embed_model,
        buffer_size=1,
        breakpoint_percentile_threshold=95
    )

    # Convert extracted text into a LlamaIndex document
    document = Document(text=text)

    # Generate semantic chunks
    nodes = splitter.get_nodes_from_documents([document])

    # Extract text from each chunk
    chunks = [node.get_content() for node in nodes]

    return chunks
