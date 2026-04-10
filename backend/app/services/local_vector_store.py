"""
Local Vector Store
===================
In-memory vector store with disk persistence using numpy cosine similarity.
Drop-in replacement for Qdrant when no external vector DB is available.

Vectors are stored in memory and persisted to a JSON file on disk so they
survive restarts. All operations are thread-safe.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("local_vector_store")


class LocalVectorStore:
    """
    Simple in-memory vector store with cosine similarity search.

    Data is persisted to a JSON file so vectors survive process restarts.
    Thread-safe for concurrent reads and writes.
    """

    def __init__(self, persist_path: Path) -> None:
        self._persist_path = persist_path
        self._lock = threading.Lock()

        # Internal store: { collection_name: { point_id: { "vector": [...], "payload": {...} } } }
        self._collections: dict[str, dict[str, dict[str, Any]]] = {}
        self._collection_configs: dict[str, dict[str, Any]] = {}

        self._load_from_disk()
        logger.info(
            "LocalVectorStore initialized (persist=%s, collections=%d)",
            self._persist_path,
            len(self._collections),
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> None:
        """Load persisted data from disk if it exists."""
        if not self._persist_path.exists():
            return
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            self._collections = data.get("collections", {})
            self._collection_configs = data.get("configs", {})
            total_points = sum(len(pts) for pts in self._collections.values())
            logger.info(
                "Loaded %d points across %d collections from disk.",
                total_points,
                len(self._collections),
            )
        except Exception as exc:
            logger.warning("Failed to load vector store from disk: %s", exc)

    def _save_to_disk(self) -> None:
        """Persist current state to disk (called after every write)."""
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "collections": self._collections,
                "configs": self._collection_configs,
            }
            self._persist_path.write_text(
                json.dumps(data, separators=(",", ":")),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Failed to persist vector store: %s", exc)

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_collection(
        self, name: str, vector_size: int, distance: str = "Cosine"
    ) -> None:
        """Create a collection if it doesn't exist. Validate size if it does."""
        with self._lock:
            if name in self._collection_configs:
                existing_size = self._collection_configs[name].get("size")
                if existing_size is not None and existing_size != vector_size:
                    raise ValueError(
                        f"Collection '{name}' has vector size {existing_size}, "
                        f"expected {vector_size}."
                    )
                return

            self._collection_configs[name] = {
                "size": vector_size,
                "distance": distance,
            }
            self._collections.setdefault(name, {})
            self._save_to_disk()
            logger.info(
                "Created collection '%s' (size=%d, distance=%s)",
                name, vector_size, distance,
            )

    def get_collection_info(self, name: str) -> dict[str, Any] | None:
        """Return collection config or None if it doesn't exist."""
        config = self._collection_configs.get(name)
        if config is None:
            return None
        return {
            "result": {
                "config": {
                    "params": {
                        "vectors": config,
                    }
                }
            }
        }

    # ------------------------------------------------------------------
    # Point operations
    # ------------------------------------------------------------------

    def upsert_points(
        self, collection: str, points: list[dict[str, Any]]
    ) -> None:
        """Insert or update points in a collection."""
        with self._lock:
            store = self._collections.setdefault(collection, {})
            for point in points:
                point_id = str(point["id"])
                store[point_id] = {
                    "vector": point["vector"],
                    "payload": point.get("payload", {}),
                }
            self._save_to_disk()

    def delete_by_filter(
        self, collection: str, filter_key: str, filter_value: str
    ) -> int:
        """Delete points matching a payload filter. Returns count deleted."""
        with self._lock:
            store = self._collections.get(collection, {})
            to_delete = [
                pid
                for pid, data in store.items()
                if data.get("payload", {}).get(filter_key) == filter_value
            ]
            for pid in to_delete:
                del store[pid]
            if to_delete:
                self._save_to_disk()
            return len(to_delete)

    def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int = 5,
        filter_key: str | None = None,
        filter_value: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for the most similar vectors using cosine similarity.

        Returns results in the same format as Qdrant's search response:
        [{"id": ..., "score": ..., "payload": {...}}, ...]
        """
        with self._lock:
            store = self._collections.get(collection, {})
            if not store:
                return []

            # Filter points
            candidates = []
            for pid, data in store.items():
                if filter_key and filter_value:
                    if data.get("payload", {}).get(filter_key) != filter_value:
                        continue
                candidates.append((pid, data))

            if not candidates:
                return []

            # Build matrix and compute cosine similarity
            query_vec = np.array(vector, dtype=np.float32)
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                return []
            query_vec = query_vec / query_norm

            ids = []
            payloads = []
            matrix = []
            for pid, data in candidates:
                ids.append(pid)
                payloads.append(data["payload"])
                matrix.append(data["vector"])

            mat = np.array(matrix, dtype=np.float32)
            # Normalize rows
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms == 0] = 1  # avoid division by zero
            mat = mat / norms

            # Cosine similarity = dot product of normalized vectors
            scores = mat @ query_vec

            # Get top_k indices
            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                results.append({
                    "id": ids[idx],
                    "score": float(scores[idx]),
                    "payload": payloads[idx],
                })

            return results

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Return store statistics."""
        return {
            "backend": "LocalVectorStore",
            "persist_path": str(self._persist_path),
            "collections": {
                name: len(points)
                for name, points in self._collections.items()
            },
        }
