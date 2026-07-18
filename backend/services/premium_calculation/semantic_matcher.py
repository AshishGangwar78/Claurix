"""
Semantic similarity matching via embeddings + cosine similarity.

Uses sentence-transformers when available; falls back to a lightweight
character n-gram TF embedding so the module remains usable offline.
"""

from functools import lru_cache
from typing import List, Optional, Tuple

import numpy as np


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _char_ngrams(text: str, n: int = 3) -> List[str]:
    cleaned = f"  {text.lower()}  "
    return [cleaned[i : i + n] for i in range(max(len(cleaned) - n + 1, 0))]


def _hash_embed(text: str, dim: int = 256) -> np.ndarray:
    """Deterministic bag-of-character-ngram embedding (fallback)."""
    vec = np.zeros(dim, dtype=np.float64)
    for gram in _char_ngrams(text):
        idx = hash(gram) % dim
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    if norm:
        vec /= norm
    return vec


class SemanticMatcher:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._backend = "fallback"
        self._prototype_cache: dict = {}

    def _load_model(self):
        if self._model is not None or self._backend == "fallback_checked":
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._backend = "sentence_transformers"
        except Exception:
            self._model = None
            self._backend = "fallback_checked"

    def embed(self, texts: List[str]) -> np.ndarray:
        self._load_model()
        if self._backend == "sentence_transformers" and self._model is not None:
            vectors = self._model.encode(texts, normalize_embeddings=True)
            return np.asarray(vectors, dtype=np.float64)

        return np.vstack([_hash_embed(t) for t in texts])

    def best_similarity(
        self,
        cell_text: str,
        prototypes: List[str],
    ) -> Tuple[float, str]:
        text = str(cell_text or "").strip()
        if not text or not prototypes:
            return 0.0, ""

        cache_key = tuple(prototypes)
        if cache_key not in self._prototype_cache:
            self._prototype_cache[cache_key] = self.embed(list(prototypes))

        cell_vec = self.embed([text])[0]
        proto_vecs = self._prototype_cache[cache_key]

        best_score = 0.0
        best_proto = ""
        for idx, proto_vec in enumerate(proto_vecs):
            score = _cosine_similarity(cell_vec, proto_vec)
            # Clamp tiny negatives from float noise
            score = max(0.0, min(1.0, score))
            if score > best_score:
                best_score = score
                best_proto = prototypes[idx]

        return best_score, best_proto


@lru_cache(maxsize=2)
def get_semantic_matcher(model_name: str) -> SemanticMatcher:
    return SemanticMatcher(model_name=model_name)
