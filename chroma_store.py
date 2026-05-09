"""
Handles all ChromaDB operations:
  - Initialize persistent ChromaDB client + collection
  - Chunk meeting notes by paragraph
  - Embed chunks using SentenceTransformers (local, no API key needed)
  - Store / query chunks
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List

# ------------------------------------------------------------------ #
#  Constants                                                          #
# ------------------------------------------------------------------ #
CHROMA_PATH = "./chroma_db"          # folder where ChromaDB saves data on disk
COLLECTION_NAME = "meeting_notes"    # name of the vector collection
EMBED_MODEL = "all-MiniLM-L6-v2"    # lightweight local embedding model (~80MB)
MIN_CHUNK_LENGTH = 30                # ignore chunks shorter than this (noise)

# ------------------------------------------------------------------ #
#  Module-level singletons (initialized once per session)            #
# ------------------------------------------------------------------ #
_chroma_client = None
_collection = None
_embed_model = None  # lazy-loaded SentenceTransformer


def _get_embed_model() -> SentenceTransformer:
    """Lazy-load SentenceTransformer model on first use."""
    global _embed_model
    if _embed_model is None:
        # Downloads model to ~/.cache on first call
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def init_chroma():
    """
    Initialize ChromaDB PersistentClient and get/create collection.
    Called once when the app starts or when a new file is uploaded.
    Returns the collection object.
    """
    global _chroma_client, _collection

    # PersistentClient saves data to disk at CHROMA_PATH
    _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    # get_or_create_collection: safe to call multiple times
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # cosine similarity for semantic search
    )

    return _collection


def _chunk_text(text: str) -> List[str]:
    """
    Split meeting notes into meaningful chunks by paragraph.
    Filters out very short chunks (headers, blank lines, etc.)
    """
    # Split on double newlines (paragraph breaks)
    raw_chunks = text.split("\n\n")

    chunks = []
    for chunk in raw_chunks:
        cleaned = chunk.strip()
        # Only keep chunks with enough content
        if len(cleaned) >= MIN_CHUNK_LENGTH:
            chunks.append(cleaned)

    return chunks


def store_meeting_notes(content: str):
    """
    PUBLIC — Called after file upload.
    Steps:
      1. Reset collection (delete old data to avoid duplicates)
      2. Chunk the meeting notes text
      3. Embed each chunk with SentenceTransformers
      4. Upsert into ChromaDB with unique IDs
    """
    global _collection

    # Ensure collection is initialized
    if _collection is None:
        init_chroma()

    # Step 1: Clear old data from previous uploads
    # delete_collection + recreate is the safest reset method
    _chroma_client.delete_collection(name=COLLECTION_NAME)
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # Step 2: Chunk the text
    chunks = _chunk_text(content)

    if not chunks:
        return  # nothing to store

    # Step 3: Generate embeddings locally (no API call)
    model = _get_embed_model()
    embeddings = model.encode(chunks, show_progress_bar=False).tolist()

    # Step 4: Upsert into ChromaDB
    # IDs must be unique strings — use "chunk_0", "chunk_1", ...
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    _collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"index": i} for i in range(len(chunks))]
    )


def query_relevant_chunks(question: str, n_results: int = 3) -> List[str]:
    """
    PUBLIC — Called before building context for OpenAI chat.
    Embeds the user question and finds top-N most similar chunks.
    Returns list of relevant text chunks.
    """
    if _collection is None:
        return []

    # Check if collection has any documents
    if _collection.count() == 0:
        return []

    # Embed the question using the same local model
    model = _get_embed_model()
    question_embedding = model.encode([question]).tolist()

    # Query ChromaDB for nearest neighbors
    results = _collection.query(
        query_embeddings=question_embedding,
        n_results=min(n_results, _collection.count()),  # avoid requesting more than available
        include=["documents"]
    )

    # results["documents"] is a list of lists — flatten to 1D
    chunks = results["documents"][0] if results["documents"] else []
    return chunks


def get_all_chunks() -> List[str]:
    """
    PUBLIC — Used by the Knowledge Base tab in the UI.
    Returns all stored chunks from ChromaDB for display.
    """
    if _collection is None or _collection.count() == 0:
        return []

    # get() with no filter returns everything
    result = _collection.get(include=["documents"])
    return result["documents"] if result["documents"] else []


def get_all_embeddings():
    """
    PUBLIC — Used by the Embeddings Visualization tab.
    Returns (chunks, embeddings) tuple for 2D plotting.
    """
    if _collection is None or _collection.count() == 0:
        return [], []

    result = _collection.get(include=["documents", "embeddings"])
    docs = result["documents"] if result["documents"] is not None else []
    embs = result["embeddings"] if result["embeddings"] is not None else []
    return docs, embs