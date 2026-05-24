"""
services/knowledge_base_service.py

Retrieves relevant FCA regulatory context from ChromaDB
to augment the compliance agent's analysis (RAG pattern).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config


def _get_client():
    try:
        import chromadb
        from chromadb.config import Settings
        return chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    except ImportError:
        raise ImportError("chromadb not installed. Run: pip install chromadb")


def _get_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(config.EMBEDDING_MODEL)
    except ImportError:
        raise ImportError("sentence-transformers not installed.")


# Cache embedder to avoid reloading on every call
_embedder_cache = None

def _embedder():
    global _embedder_cache
    if _embedder_cache is None:
        _embedder_cache = _get_embedder()
    return _embedder_cache


def query_collection(collection_name: str, query: str, n_results: int = None) -> str:
    """
    Query a ChromaDB collection and return formatted context string.
    """
    n = n_results or config.KB_TOP_K
    client = _get_client()

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return f"[KB] Collection '{collection_name}' not found. Run ingest_kb.py first."

    embedding = _embedder().encode([query]).tolist()
    results = collection.query(query_embeddings=embedding, n_results=n)

    if not results["documents"] or not results["documents"][0]:
        return "[KB] No relevant regulatory context found."

    chunks = results["documents"][0]
    sources = [m.get("source_file", "unknown") for m in results["metadatas"][0]]

    formatted = []
    for i, (chunk, source) in enumerate(zip(chunks, sources), 1):
        formatted.append(f"[Rule {i} — {source}]\n{chunk.strip()}")

    return "\n\n".join(formatted)


def get_compliance_context(transcript: str) -> str:
    """
    Build a combined regulatory context string for the compliance agent
    by querying all relevant collections based on transcript content.
    Returns formatted context ready to inject into the compliance prompt.
    """
    contexts = []

    # Always query Consumer Duty (covers most compliance scenarios)
    cd_context = query_collection(
        config.CHROMA_COLLECTION_FCA_CONSUMER_DUTY,
        query=transcript[:1000],  # use first 1000 chars as query — captures scenario type
    )
    if cd_context:
        contexts.append(f"=== FCA Consumer Duty ===\n{cd_context}")

    # Query vulnerable customer guidance
    vc_context = query_collection(
        config.CHROMA_COLLECTION_VULNERABLE_CUSTOMERS,
        query="vulnerable customer consent confusion elderly bereavement",
    )
    if vc_context:
        contexts.append(f"=== FCA Vulnerable Customer Guidance ===\n{vc_context}")

    # Query call recording / GDPR
    cr_context = query_collection(
        config.CHROMA_COLLECTION_CALL_RECORDING,
        query="identity verification data disclosure account number sort code GDPR",
    )
    if cr_context:
        contexts.append(f"=== FCA SYSC 9 / UK GDPR ===\n{cr_context}")

    return "\n\n".join(contexts) if contexts else "No regulatory context retrieved."
