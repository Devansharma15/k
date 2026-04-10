"""
Local Embedding Service
========================
Production-ready, fully offline embedding module using sentence-transformers.

Features:
  - Singleton model instance (loaded once, reused across all calls)
  - Configurable model via EMBEDDING_MODEL env var
  - L2-normalized embeddings (cosine-similarity ready)
  - Single-text and batch embedding APIs
  - Graceful error handling with structured logging
  - Drop-in replacement for OpenAI embeddings — same interface shape

Supported models (set EMBEDDING_MODEL env var):
  - "all-MiniLM-L6-v2"      (default, 384-dim, fastest)
  - "all-mpnet-base-v2"      (768-dim, higher quality)
  - "all-distilroberta-v1"   (768-dim, balanced)

Usage:
    from app.services.embedding_service import embedding_service

    vector = embedding_service.embed("some text")
    vectors = embedding_service.embed_batch(["text1", "text2"])
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Model to load. Override via environment variable for easy upgrades.
DEFAULT_MODEL_NAME: str = "all-MiniLM-L6-v2"

# Dimension lookup for common models (used as fallback when model isn't loaded)
MODEL_DIMENSIONS: dict[str, int] = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
    "all-distilroberta-v1": 768,
}

# Batch size for `encode()` — balances memory and throughput
DEFAULT_BATCH_SIZE: int = 32

# Module-level logger
logger = logging.getLogger("embedding_service")

# ---------------------------------------------------------------------------
# Embedding Service
# ---------------------------------------------------------------------------


class LocalEmbeddingService:
    """
    Singleton-style local embedding service backed by sentence-transformers.

    The underlying SentenceTransformer model is loaded lazily on the first
    call and reused for the lifetime of the process.  Thread-safe.
    """

    def __init__(self, model_name: str | None = None) -> None:
        # Allow override via constructor arg → env var → default constant
        self._model_name: str = (
            model_name
            or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL_NAME)
        )
        self._model: Any | None = None
        self._lock = threading.Lock()  # guards lazy model init

        logger.info(
            "LocalEmbeddingService configured with model='%s'",
            self._model_name,
        )

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    def _load_model(self) -> Any:
        """
        Lazily load the SentenceTransformer model (thread-safe, exactly once).
        """
        if self._model is not None:
            return self._model

        with self._lock:
            # Double-checked locking
            if self._model is not None:
                return self._model

            logger.info("Loading embedding model '%s' …", self._model_name)

            # --- Import guard ---
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                logger.error(
                    "sentence-transformers package is not installed. "
                    "Run: pip install sentence-transformers"
                )
                raise RuntimeError(
                    "sentence-transformers is required for local embeddings. "
                    "Install it with: pip install sentence-transformers"
                ) from exc

            # --- Model loading ---
            try:
                self._model = SentenceTransformer(self._model_name)
                logger.info(
                    "Model '%s' loaded successfully (dimension=%s).",
                    self._model_name,
                    self._model.get_sentence_embedding_dimension(),
                )
            except Exception as exc:
                logger.error(
                    "Failed to load model '%s': %s", self._model_name, exc
                )
                raise RuntimeError(
                    f"Failed to load embedding model '{self._model_name}'. "
                    f"Ensure the model name is valid and you have internet "
                    f"access for the initial download."
                ) from exc

        return self._model

    @property
    def model_name(self) -> str:
        """Return the configured model name."""
        return self._model_name

    @property
    def is_loaded(self) -> bool:
        """Check whether the model has already been loaded into memory."""
        return self._model is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        """
        Embed a single text string and return a normalized float vector.

        This is the primary method for query-time embedding.

        Args:
            text: The input string to embed.

        Returns:
            A list of floats representing the L2-normalized embedding.

        Raises:
            ValueError:  If ``text`` is empty or not a string.
            RuntimeError: If the model fails to produce an embedding.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("embed() requires a non-empty string.")

        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(
        self,
        texts: list[str],
        *,
        batch_size: int | None = None,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Embed a list of texts and return normalized float vectors.

        This is the primary method for ingestion-time embedding.

        Args:
            texts:          List of input strings.
            batch_size:     Override the default batch size for this call.
            show_progress:  Show a tqdm progress bar (useful for large jobs).

        Returns:
            A list of float-vectors, one per input text.

        Raises:
            ValueError:  If ``texts`` is empty.
            RuntimeError: If the model fails to produce embeddings.
        """
        if not texts:
            return []

        model = self._load_model()
        effective_batch_size = batch_size or DEFAULT_BATCH_SIZE

        try:
            embeddings = model.encode(
                texts,
                batch_size=effective_batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True,   # L2 normalization for cosine sim
                convert_to_numpy=True,
            )
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise RuntimeError(
                "Failed to generate embeddings. See logs for details."
            ) from exc

        # Convert numpy ndarray → list[list[float]]
        if hasattr(embeddings, "tolist"):
            result = embeddings.tolist()
        else:
            result = [list(map(float, vec)) for vec in embeddings]

        if not result:
            raise RuntimeError("Embedding model returned no vectors.")

        # Ensure all values are native Python floats (JSON-serializable)
        return [
            [float(v) for v in vector]
            for vector in result
        ]

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Alias for ``embed_batch`` — preserves backward compatibility with
        the previous API surface used by knowledge_base_service.
        """
        return self.embed_batch(texts)

    def vector_size(self) -> int:
        """
        Return the dimensionality of the embedding vectors.

        If the model is already loaded, queries it directly.
        Otherwise falls back to the known dimension table.
        """
        if self._model is not None:
            dim_fn = getattr(self._model, "get_sentence_embedding_dimension", None)
            if callable(dim_fn):
                size = dim_fn()
                if isinstance(size, int) and size > 0:
                    return size

        # Fallback: look up from known models
        return MODEL_DIMENSIONS.get(self._model_name, 384)

    def health_check(self) -> dict[str, Any]:
        """
        Return a diagnostic dict — useful for /health endpoints.
        """
        return {
            "service": "LocalEmbeddingService",
            "model": self._model_name,
            "loaded": self.is_loaded,
            "vector_size": self.vector_size(),
            "backend": "sentence-transformers",
        }

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "loaded" if self.is_loaded else "not loaded"
        return (
            f"<LocalEmbeddingService model='{self._model_name}' "
            f"dim={self.vector_size()} {status}>"
        )


# ---------------------------------------------------------------------------
# Module-level singleton instance
# ---------------------------------------------------------------------------
# Import this in other modules:
#     from app.services.embedding_service import embedding_service
#
# The model is NOT loaded at import time — only on the first embed() call.

embedding_service = LocalEmbeddingService()

# Re-export the default model name for backward compatibility
DEFAULT_LOCAL_EMBEDDING_MODEL = embedding_service.model_name

class LocalCrossEncoderService:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _load_model(self):
        if self._model is not None:
            return self._model
        
        with self._lock:
            if self._model is None:
                logger.info(f"Loading Cross-Encoder model: {self._model_name}")
                try:
                    from sentence_transformers import CrossEncoder
                    self._model = CrossEncoder(self._model_name)
                    logger.info("Cross-Encoder model loaded successfully.")
                except ImportError as exc:
                    raise RuntimeError("sentence-transformers is required.") from exc
                except Exception as exc:
                    logger.error(f"Failed to load Cross-Encoder model: {exc}")
                    raise RuntimeError("Failed to load Cross-Encoder.") from exc
        return self._model

    def predict(self, pairs: list[list[str]]) -> list[float]:
        if not pairs:
            return []
        model = self._load_model()
        scores = model.predict(pairs)
        if hasattr(scores, "tolist"):
            return scores.tolist()
        return [float(s) for s in scores]

cross_encoder_service = LocalCrossEncoderService()
