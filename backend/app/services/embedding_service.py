from __future__ import annotations

from typing import Any

DEFAULT_LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_LOCAL_EMBEDDING_DIMENSION = 384
DEFAULT_EMBED_BATCH_SIZE = 20


class LocalEmbeddingService:
    def __init__(self) -> None:
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for local Knowledge Base embeddings."
            ) from exc

        try:
            self._model = SentenceTransformer(DEFAULT_LOCAL_EMBEDDING_MODEL)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load local embedding model '{DEFAULT_LOCAL_EMBEDDING_MODEL}'."
            ) from exc

        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = self._get_model()
        try:
            embeddings = model.encode(
                texts,
                batch_size=DEFAULT_EMBED_BATCH_SIZE,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
        except Exception as exc:
            raise RuntimeError("Failed to generate local embeddings.") from exc

        if hasattr(embeddings, "tolist"):
            embeddings = embeddings.tolist()

        if not embeddings:
            raise RuntimeError("Local embedding model returned no vectors.")

        return [
            [float(value) for value in embedding]
            for embedding in embeddings
        ]

    def vector_size(self) -> int:
        model = self._get_model()
        dimension = getattr(model, "get_sentence_embedding_dimension", None)
        if callable(dimension):
            size = dimension()
            if isinstance(size, int) and size > 0:
                return size
        return DEFAULT_LOCAL_EMBEDDING_DIMENSION


embedding_service = LocalEmbeddingService()
