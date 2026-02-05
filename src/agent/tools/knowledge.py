import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

# Initialize persistent ChromaDB client
# Note: We should ideally move this path to config
chroma_client = chromadb.PersistentClient(path="./knowledge_db")
sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(name="coffee_knowledge", embedding_function=sentence_transformer_ef)

@tool
def add_knowledge(topic: str, content: str):
    """Teaches the AI a new fact or procedure. 'topic' is a short ID, 'content' is the full info."""
    collection.upsert(
        documents=[content],
        metadatas=[{"topic": topic}],
        ids=[topic]
    )
    return f"Đã ghi nhớ kiến thức: [{topic}]"

@tool
def query_knowledge(query: str):
    """Searches the internal knowledge base for information."""
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    if not results['documents'] or not results['documents'][0]:
        return "Không tìm thấy thông tin liên quan."
    return "\n\n".join(results['documents'][0])
