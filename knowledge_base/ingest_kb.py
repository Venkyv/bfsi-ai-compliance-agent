"""
knowledge_base/ingest_kb.py

Ingests FCA regulatory documents into ChromaDB collections.
Run this once before starting Sprint 1.

Usage:
    python knowledge_base/ingest_kb.py
    python knowledge_base/ingest_kb.py --reset   # wipe and re-ingest
"""

import os
import sys
import argparse

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config


# Document → collection mapping
KB_DOCUMENTS = [
    {
        "file": "fca_consumer_duty.txt",
        "collection": config.CHROMA_COLLECTION_FCA_CONSUMER_DUTY,
        "description": "FCA Consumer Duty — Final Rules and Guidance (PS22/9)",
    },
    {
        "file": "fca_vulnerable_customers.txt",
        "collection": config.CHROMA_COLLECTION_VULNERABLE_CUSTOMERS,
        "description": "FCA FG21/1 — Fair Treatment of Vulnerable Customers",
    },
    {
        "file": "fca_call_recording.txt",
        "collection": config.CHROMA_COLLECTION_CALL_RECORDING,
        "description": "FCA SYSC 9 — Call Recording and UK GDPR Data Obligations",
    },
    {
        "file": "fca_app_fraud.txt",
        "collection": config.CHROMA_COLLECTION_FCA_CONSUMER_DUTY,  # stored in consumer duty collection
        "description": "FCA / PSR — APP Fraud Guidance and Agent Obligations",
    },
]


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Try to end on a sentence boundary
        if end < len(text):
            last_period = chunk.rfind(". ")
            if last_period > chunk_size // 2:
                chunk = chunk[:last_period + 1]
                end = start + last_period + 1
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if len(c) > 50]  # drop tiny fragments


def ingest(reset: bool = False) -> None:
    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("Run: pip install chromadb sentence-transformers")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("BFSI Compliance Agent — Knowledge Base Ingest")
    print(f"{'='*60}")
    print(f"ChromaDB dir : {config.CHROMA_PERSIST_DIR}")
    print(f"Embedding    : {config.EMBEDDING_MODEL}")
    print(f"Chunk size   : {config.EMBEDDING_CHUNK_SIZE} chars")
    print(f"Overlap      : {config.EMBEDDING_CHUNK_OVERLAP} chars")
    print(f"Reset mode   : {reset}")
    print()

    # Initialise ChromaDB
    client = chromadb.PersistentClient(
        path=config.CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )

    # Initialise embedding model
    print(f"Loading embedding model: {config.EMBEDDING_MODEL}...")
    embedder = SentenceTransformer(config.EMBEDDING_MODEL)
    print("Model loaded.\n")

    kb_dir = os.path.join(os.path.dirname(__file__))
    total_chunks = 0

    for doc in KB_DOCUMENTS:
        filepath = os.path.join(kb_dir, doc["file"])

        if not os.path.exists(filepath):
            print(f"[SKIP] File not found: {filepath}")
            continue

        print(f"Processing: {doc['file']}")
        print(f"  Collection : {doc['collection']}")
        print(f"  Description: {doc['description']}")

        # Read document
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Get or create collection
        if reset:
            try:
                client.delete_collection(doc["collection"])
                print(f"  Deleted existing collection: {doc['collection']}")
            except Exception:
                pass

        collection = client.get_or_create_collection(
            name=doc["collection"],
            metadata={"description": doc["description"]},
        )

        # Chunk text
        chunks = chunk_text(text, config.EMBEDDING_CHUNK_SIZE, config.EMBEDDING_CHUNK_OVERLAP)
        print(f"  Chunks     : {len(chunks)}")

        # Embed and store
        embeddings = embedder.encode(chunks, show_progress_bar=False).tolist()

        ids = [f"{doc['file'].replace('.txt', '')}_{i:04d}" for i in range(len(chunks))]
        metadatas = [
            {
                "source_file": doc["file"],
                "collection_label": doc["collection"],
                "chunk_index": i,
                "description": doc["description"],
            }
            for i in range(len(chunks))
        ]

        # Add in batches to avoid memory issues
        batch_size = 50
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            collection.add(
                ids=ids[batch_start:batch_end],
                embeddings=embeddings[batch_start:batch_end],
                documents=chunks[batch_start:batch_end],
                metadatas=metadatas[batch_start:batch_end],
            )

        total_chunks += len(chunks)
        print(f"  Status     : ✓ Ingested {len(chunks)} chunks\n")

    print(f"{'='*60}")
    print(f"Ingest complete. Total chunks stored: {total_chunks}")
    print(f"ChromaDB persisted at: {config.CHROMA_PERSIST_DIR}")
    print(f"{'='*60}\n")

    # Verification query
    print("Running verification query...")
    verify_collection = client.get_or_create_collection(config.CHROMA_COLLECTION_FCA_CONSUMER_DUTY)
    test_query = "What are the requirements when an investment product is described as risk-free?"
    test_embedding = embedder.encode([test_query]).tolist()
    results = verify_collection.query(
        query_embeddings=test_embedding,
        n_results=2,
    )
    print(f"Query: '{test_query}'")
    print(f"Top result preview: {results['documents'][0][0][:200]}...")
    print("\nKnowledge base ready for Sprint 1.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest FCA knowledge base into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collections and re-ingest from scratch",
    )
    args = parser.parse_args()
    ingest(reset=args.reset)
