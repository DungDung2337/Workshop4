"""
In-memory vector store using FAISS + SentenceTransformers.
Chunks meeting notes by paragraph, embeds with all-MiniLM-L6-v2,
and indexes with FAISS IndexFlatIP (cosine similarity via L2 normalization).
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

EMBED_MODEL = "all-MiniLM-L6-v2"
MIN_CHUNK_LENGTH = 30

_model = None
_chunks: List[str] = []
_embeddings: List[List[float]] = []   # kept for visualization (get_all_embeddings)
_index = None                          # faiss.IndexFlatIP, built on store


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _chunk_text(text: str) -> List[str]:
    return [
        c.strip()
        for c in text.split("\n\n")
        if len(c.strip()) >= MIN_CHUNK_LENGTH
    ]


def _encode(texts: List[str]) -> np.ndarray:
    """Encode texts to L2-normalized float32 vectors (cosine via inner product)."""
    embs = _get_model().encode(texts, show_progress_bar=False).astype("float32")
    faiss.normalize_L2(embs)
    return embs


def init_store():
    pass


def store_meeting_notes(content: str):
    global _chunks, _embeddings, _index
    _chunks = _chunk_text(content)
    if not _chunks:
        _embeddings = []
        _index = None
        return
    embs = _encode(_chunks)
    _embeddings = embs.tolist()
    _index = faiss.IndexFlatIP(embs.shape[1])
    _index.add(embs)


def query_relevant_chunks(question: str, n_results: int = 3) -> List[str]:
    if _index is None or not _chunks:
        return []
    q = _encode([question])
    top_k = min(n_results, len(_chunks))
    _, indices = _index.search(q, top_k)
    return [_chunks[i] for i in indices[0] if i >= 0]


def get_all_chunks() -> List[str]:
    return _chunks


def get_all_embeddings():
    return _chunks, _embeddings
