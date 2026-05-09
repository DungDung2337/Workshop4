"""
In-memory vector store using numpy + SentenceTransformers.
Replaces ChromaDB to avoid opentelemetry/protobuf Python 3.14 incompatibility.
Same public interface as before — no changes needed in main.py or chain_builder.py.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

EMBED_MODEL = "all-MiniLM-L6-v2"
MIN_CHUNK_LENGTH = 30

_model = None
_chunks: List[str] = []
_embeddings: List[List[float]] = []


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


def init_chroma():
    pass


def store_meeting_notes(content: str):
    global _chunks, _embeddings
    _chunks = _chunk_text(content)
    if not _chunks:
        _embeddings = []
        return
    model = _get_model()
    _embeddings = model.encode(_chunks, show_progress_bar=False).tolist()


def query_relevant_chunks(question: str, n_results: int = 3) -> List[str]:
    if not _chunks or not _embeddings:
        return []
    model = _get_model()
    q_emb = model.encode([question])[0]
    embs = np.array(_embeddings)
    norms = np.linalg.norm(embs, axis=1) * np.linalg.norm(q_emb) + 1e-9
    scores = embs @ q_emb / norms
    top_k = min(n_results, len(_chunks))
    top_idx = np.argsort(scores)[::-1][:top_k]
    return [_chunks[i] for i in top_idx]


def get_all_chunks() -> List[str]:
    return _chunks


def get_all_embeddings():
    return _chunks, _embeddings
