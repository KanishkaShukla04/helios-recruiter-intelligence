"""
semantic_score.py — Helios Recruiter Intelligence
==================================================
Computes semantic similarity between a Job Description and candidate profiles
using Sentence Transformers (all-MiniLM-L6-v2).

Design goals
------------
* CPU-compatible, no GPU required.
* Efficient for 100,000+ candidates via batch embedding.
* LRU + optional disk cache to avoid re-embedding identical texts.
* Cosine similarity via pure NumPy (no heavy torch dependency at inference).

Usage::

    from app.scoring.semantic_score import SemanticScorer

    scorer = SemanticScorer()
    jd_text  = "Senior ML Engineer — RAG, LLMs, Python …"
    profiles = ["6 years Python, PyTorch, RAG pipelines …", "…", …]

    # Single candidate
    score = scorer.score_one(jd_text, profiles[0])

    # Bulk (100k candidates)
    scores = scorer.score_bulk(jd_text, profiles)  # np.ndarray of floats
"""

from __future__ import annotations

import hashlib
import logging
import os
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# Batch size tuned for 512 MB RAM budget on CPU
DEFAULT_BATCH_SIZE: int = int(os.getenv("HELIOS_EMBED_BATCH_SIZE", "256"))

# On-disk cache directory (set to "" to disable)
CACHE_DIR: str = os.getenv("HELIOS_EMBED_CACHE_DIR", "/tmp/helios_embed_cache")

# In-process LRU cache size (number of unique texts)
LRU_MAXSIZE: int = int(os.getenv("HELIOS_EMBED_LRU_SIZE", "4096"))

# ---------------------------------------------------------------------------
# Lazy model loader — loaded once per process
# ---------------------------------------------------------------------------

_MODEL_INSTANCE: Optional[object] = None  # SentenceTransformer instance


def _get_model():
    """
    Return (and lazy-load) the sentence transformer model.
    Thread-safe via Python GIL for the singleton pattern.
    """
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            logger.info("Loading embedding model: %s", MODEL_NAME)
            _MODEL_INSTANCE = SentenceTransformer(MODEL_NAME, device="cpu")
            logger.info("Model loaded successfully.")
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc
    return _MODEL_INSTANCE


# ---------------------------------------------------------------------------
# Disk cache helpers
# ---------------------------------------------------------------------------


def _text_hash(text: str) -> str:
    """SHA-256 hex digest of the input text (used as cache key)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cache_path(text_hash: str) -> Path:
    return Path(CACHE_DIR) / f"{text_hash}.pkl"


def _load_from_disk(text_hash: str) -> Optional[np.ndarray]:
    path = _cache_path(text_hash)
    if path.exists():
        try:
            with path.open("rb") as f:
                return pickle.load(f)  # noqa: S301
        except (OSError, pickle.UnpicklingError):
            logger.warning("Corrupted cache entry: %s", path)
    return None


def _save_to_disk(text_hash: str, embedding: np.ndarray) -> None:
    if not CACHE_DIR:
        return
    try:
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        with _cache_path(text_hash).open("wb") as f:
            pickle.dump(embedding, f)
    except OSError as exc:
        logger.warning("Could not write embedding cache: %s", exc)


# ---------------------------------------------------------------------------
# Core embedding function (in-process LRU cache)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=LRU_MAXSIZE)
def _embed_single_cached(text: str) -> np.ndarray:
    """
    Embed a single text with full caching (LRU in memory + disk).
    The ``@lru_cache`` keyed on the text string handles repeated identical
    inputs within a session without re-encoding.
    """
    h = _text_hash(text)

    # 1. Disk cache
    cached = _load_from_disk(h)
    if cached is not None:
        return cached

    # 2. Model inference
    model = _get_model()
    embedding: np.ndarray = model.encode(
        [text],
        batch_size=1,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  # unit vectors → cosine = dot product
    )[0]

    _save_to_disk(h, embedding)
    return embedding


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity between two L2-normalised vectors.
    Since embeddings are pre-normalised, this reduces to a dot product.
    """
    return float(np.dot(a, b))


def _cosine_similarity_matrix(
    query: np.ndarray, matrix: np.ndarray
) -> np.ndarray:
    """
    Vectorised cosine similarity of a single query against a (N, D) matrix.
    Both inputs must be L2-normalised.
    Returns a (N,) array of similarity scores in [-1, 1].
    """
    return matrix @ query  # (N, D) × (D,) → (N,)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class SemanticScorer:
    """
    Semantic similarity scorer for JD ↔ candidate profile matching.

    Parameters
    ----------
    batch_size:
        Number of candidate texts embedded in each forward pass.
        Tune based on available RAM.  Default: 256.

    Example::

        scorer = SemanticScorer()
        score  = scorer.score_one(jd_text, candidate_profile_text)
        scores = scorer.score_bulk(jd_text, list_of_profile_texts)
    """

    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        self.batch_size = batch_size

    # ------------------------------------------------------------------
    # Single candidate
    # ------------------------------------------------------------------

    def score_one(self, jd_text: str, candidate_text: str) -> float:
        """
        Return a similarity score in [0, 100] for a single (JD, candidate) pair.

        Parameters
        ----------
        jd_text:
            Full text of the job description.
        candidate_text:
            Concatenated candidate profile text (skills, experience, bio …).
        """
        jd_vec = _embed_single_cached(jd_text)
        cand_vec = _embed_single_cached(candidate_text)
        raw_sim = _cosine_similarity(jd_vec, cand_vec)
        return self._normalise(raw_sim)

    # ------------------------------------------------------------------
    # Bulk scoring (optimised for 100k+ candidates)
    # ------------------------------------------------------------------

    def score_bulk(
        self,
        jd_text: str,
        candidate_texts: list[str],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Compute similarity scores for a large candidate pool.

        Embeddings are generated in batches to stay within memory limits.
        The JD embedding is computed once and reused.

        Parameters
        ----------
        jd_text:
            Job description text.
        candidate_texts:
            List of candidate profile texts (can be 100k+ items).
        show_progress:
            Print tqdm progress bar (requires ``tqdm`` installed).

        Returns
        -------
        np.ndarray
            Float array of shape (N,) with scores in [0, 100].
        """
        if not candidate_texts:
            return np.array([], dtype=np.float32)

        jd_vec = _embed_single_cached(jd_text)  # shape (D,)
        n = len(candidate_texts)

        # Pre-allocate result array
        scores = np.empty(n, dtype=np.float32)

        model = _get_model()

        # Progress wrapper
        batches = range(0, n, self.batch_size)
        if show_progress:
            try:
                from tqdm import tqdm  # type: ignore

                batches = tqdm(batches, desc="Embedding candidates", unit="batch")
            except ImportError:
                logger.info("tqdm not installed — progress bar disabled.")

        for start in batches:
            end = min(start + self.batch_size, n)
            batch_texts = candidate_texts[start:end]

            # Check LRU cache for each text before calling model
            batch_vecs = self._embed_batch(model, batch_texts)  # (B, D)
            sims = _cosine_similarity_matrix(jd_vec, batch_vecs)  # (B,)
            scores[start:end] = [self._normalise(s) for s in sims]

        return scores

    # ------------------------------------------------------------------
    # Embed a batch of texts
    # ------------------------------------------------------------------

    def _embed_batch(self, model, texts: list[str]) -> np.ndarray:
        """
        Embed a list of texts.
        Texts already in the LRU cache are served from there;
        only novel texts are passed to the model.
        """
        # Split into cached and uncached
        indices_to_encode: list[int] = []
        result_vecs: list[Optional[np.ndarray]] = [None] * len(texts)

        for i, text in enumerate(texts):
            cached = _embed_single_cached.__wrapped__(text) if False else None
            # Check LRU without polluting cache for batch items
            h = _text_hash(text)
            disk_cached = _load_from_disk(h)
            if disk_cached is not None:
                result_vecs[i] = disk_cached
            else:
                indices_to_encode.append(i)

        if indices_to_encode:
            texts_to_encode = [texts[i] for i in indices_to_encode]
            encoded: np.ndarray = model.encode(
                texts_to_encode,
                batch_size=len(texts_to_encode),
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            for j, idx in enumerate(indices_to_encode):
                vec = encoded[j]
                result_vecs[idx] = vec
                # Persist to disk cache
                _save_to_disk(_text_hash(texts[idx]), vec)

        # Stack into matrix
        vecs = [
            v if v is not None else _embed_single_cached(texts[i])
            for i, v in enumerate(result_vecs)
        ]
        return np.stack(vecs, axis=0)  # (B, D)

    # ------------------------------------------------------------------
    # Embed JD and get vector (useful for pre-computing once)
    # ------------------------------------------------------------------

    def embed_jd(self, jd_text: str) -> np.ndarray:
        """Return the normalised embedding vector for a JD."""
        return _embed_single_cached(jd_text)

    def embed_profiles(self, profile_texts: list[str]) -> np.ndarray:
        """
        Batch-embed all profiles and return a (N, D) matrix.
        Useful for building an offline index.
        """
        model = _get_model()
        return self._embed_batch(model, profile_texts)

    # ------------------------------------------------------------------
    # Normalisation: cosine [-1, 1] → [0, 100]
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(cosine_sim: float) -> float:
        """
        Map cosine similarity from [-1, 1] to [0, 100].
        In practice all-MiniLM produces values in [0, 1] for typical text pairs.
        """
        return round(float(np.clip((cosine_sim + 1.0) / 2.0 * 100.0, 0.0, 100.0)), 2)

    # ------------------------------------------------------------------
    # Top-K helper
    # ------------------------------------------------------------------

    def top_k_indices(self, scores: np.ndarray, k: int) -> np.ndarray:
        """Return indices of the top-k scores in descending order."""
        k = min(k, len(scores))
        return np.argsort(scores)[::-1][:k]


# ---------------------------------------------------------------------------
# Unit-test examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    JD = (
        "Senior ML Engineer with 4+ years Python, PyTorch, transformer models, "
        "RAG pipelines, vector search (Faiss/Pinecone), AWS, Kubernetes. "
        "Experience in production LLM serving and MLflow."
    )

    PROFILES = [
        # Strong match
        "6 years of Python ML engineering. Built RAG pipeline at scale using "
        "Faiss + Pinecone. Deployed PyTorch transformer models on AWS EKS. "
        "MLflow for experiment tracking. Strong NLP background.",
        # Weak match
        "3 years Android development with Kotlin and Jetpack Compose. "
        "Built e-commerce apps. Firebase, REST APIs. No ML experience.",
        # Partial match
        "4 years data science in Python. Scikit-learn, pandas, SQL. "
        "Some exposure to PyTorch but no production model deployment.",
    ]

    scorer = SemanticScorer()
    scores = scorer.score_bulk(JD, PROFILES, show_progress=False)
    for profile, score in zip(PROFILES, scores):
        print(f"Score {score:.1f} | {profile[:60]}…")
