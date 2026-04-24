import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("faiss_store")

class FaissLocalStore:
    def __init__(self, storage_path: Path | str, dimension: int = 768):
        self.storage_path = Path(storage_path)
        self.dimension = dimension
        self.index = None
        self.payloads: dict[str, dict[str, Any]] = {}
        self.id_map: dict[int, str] = {}
        
        # We need faiss imported lazily
        self._initialize_index()
        self._load()

    def _initialize_index(self):
        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.dimension)
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required for local RAG.") from exc

    def _load(self):
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "dimension" in data and data["dimension"] != self.dimension:
                logger.warning(
                    f"Dimension mismatch in {self.storage_path}: "
                    f"expected {self.dimension}, got {data['dimension']}. Re-initializing empty."
                )
                self.payloads = {}
                self.id_map = {}
                self._initialize_index()
                return

            self.payloads = data.get("payloads", {})
            self.id_map = {int(k): v for k, v in data.get("id_map", {}).items()}
            
            vectors = data.get("vectors", [])
            if vectors:
                vec_arr = np.array(vectors, dtype=np.float32)
                self.index.add(vec_arr)
        except Exception as e:
            logger.error(f"Failed to load FAISS store from JSON: {e}")

    def _save(self):
        try:
            # Reconstruct vector array from index
            import faiss
            num_vectors = self.index.ntotal
            if num_vectors > 0:
                vectors = faiss.rev_swig_ptr(self.index.get_xb(), self.dimension * num_vectors)
                vectors = vectors.reshape((num_vectors, self.dimension)).tolist()
            else:
                vectors = []

            data = {
                "dimension": self.dimension,
                "vectors": vectors,
                "payloads": self.payloads,
                "id_map": {str(k): v for k, v in self.id_map.items()}
            }
            
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save FAISS store: {e}")

    def upsert(self, point_id: str, vector: list[float], payload: dict[str, Any]):
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dim {len(vector)} != expected {self.dimension}")

        # If it exists, currently we don't have a direct delete. We do a naive rebuild if we had to update.
        # For simplicity, if ID exists we ignore or append. Since faiss IndexFlatL2 doesn't support 
        # remove easily via string ID, we will just rebuild if we need to remove, or 
        # append a new one. In this simple demo we'll rebuild the index if it's an update.
        
        if point_id in self.payloads:
            # Overwrite payload
            self.payloads[point_id] = payload
            # We must rebuild the whole FAISS index to replace the vector
            # This is fine for small local collections.
            _all_points = []
            for internal_id_str, p_id in sorted(self.id_map.items()):
                # this is expensive.
                pass 
                
        # Simple strategy: keep a shadow dict of vectors, rebuild faiss instantly.
        # To strictly use FAISS, let's keep all vectors in Numpy, and rebuild FAISS every time we insert/delete.
        # This is safe for ~100k chunks locally.
        pass

# A fully reconstructive FAISS store.
class FaissSimpleStore:
    def __init__(self, storage_path: Path | str, dimension: int = 768):
        self.storage_path = Path(storage_path)
        self.dimension = dimension
        self.data: dict[str, dict[str, Any]] = {}
        # data[point_id] = { "vector": [...], "payload": {...} }
        self._load()

    def _load(self):
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if loaded.get("dimension") == self.dimension:
                    self.data = loaded.get("data", {})
        except Exception:
            pass

    def _save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({"dimension": self.dimension, "data": self.data}, f)

    def upsert_batch(self, ids: list[str], vectors: list[list[float]], payloads: list[dict[str, Any]]):
        for i, vec, p in zip(ids, vectors, payloads):
            self.data[i] = {"vector": vec, "payload": p}
        self._save()

    def delete_by_payload_match(self, key: str, value: str):
        to_delete = [k for k, v in self.data.items() if v["payload"].get(key) == value]
        for k in to_delete:
            del self.data[k]
        self._save()

    def search(self, query_vector: list[float], top_k: int, filter_key: str = None, filter_val: str = None) -> list[dict[str, Any]]:
        if not self.data:
            return []

        # Filter first
        candidates = []
        for k, v in self.data.items():
            if filter_key and filter_val:
                if v["payload"].get(filter_key) != filter_val:
                    continue
            candidates.append((k, v["vector"], v["payload"]))
            
        if not candidates:
            return []
            
        candidate_ids = []
        vecs = []
        for c_id, c_vec, c_payload in candidates:
            candidate_ids.append((c_id, c_payload))
            vecs.append(c_vec)
            
        vec_arr = np.array(vecs, dtype=np.float32)
        q_arr = np.array(query_vector, dtype=np.float32)
        
        # Calculate L2 squared distances (pure numpy)
        diff = vec_arr - q_arr
        distances = np.sum(diff**2, axis=-1)
        
        k = min(top_k, len(candidates))
        if k < len(candidates):
            indices = np.argpartition(distances, k)[:k]
            top_k_indices = indices[np.argsort(distances[indices])]
        else:
            top_k_indices = np.argsort(distances)
        
        results = []
        for idx in top_k_indices:
            dist = distances[idx]
            point_id, payload = candidate_ids[idx]
            results.append({
                "id": point_id,
                "score": float(1.0 / (1.0 + dist)),  # L2 inverted roughly mapping to similarity
                "payload": payload
            })
        return results
