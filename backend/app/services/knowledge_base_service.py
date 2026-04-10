from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .embedding_service import (
    DEFAULT_LOCAL_EMBEDDING_MODEL,
    embedding_service,
)


DEFAULT_USER_ID = "demo-user"
DEFAULT_EMBEDDING_MODEL = DEFAULT_LOCAL_EMBEDDING_MODEL
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
EMBEDDING_BATCH_SIZE = 20


class KnowledgeBaseConfigError(RuntimeError):
    pass


def _slugify(value: str) -> str:
    return (
        value.lower()
        .replace("&", "and")
        .replace("/", "-")
        .replace(".", "")
        .replace(" ", "-")
        .replace("--", "-")
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


SEED_DATASETS: list[dict[str, Any]] = []


@dataclass
class DatasetRecord:
    id: str
    name: str
    slug: str
    description: str
    embedding_model: str
    chunk_size: int
    user_id: str


class KnowledgeBaseService:
    def __init__(self) -> None:
        self._backend_root = Path(__file__).resolve().parents[2]
        self._repo_root = Path(__file__).resolve().parents[3]
        self._data_root = self._backend_root / "data"
        self._storage_root = self._data_root / "knowledge_base"
        self._seed_root = self._data_root / "knowledge_base_seed"
        self._db_path = self._data_root / "knowledge_base.sqlite3"
        self._collection = os.getenv(
            "QDRANT_COLLECTION",
            "auraflow_knowledge_base_local_v1",
        )
        self._storage_root.mkdir(parents=True, exist_ok=True)
        self._seed_root.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._ensure_seed_files()
        self._ensure_dataset_rows()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    chunk_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    page_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(dataset_id, file_hash),
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    vector_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS query_cache (
                    id TEXT PRIMARY KEY,
                    dataset_id TEXT NOT NULL,
                    query_hash TEXT NOT NULL,
                    query_text TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    UNIQUE(dataset_id, query_hash)
                );
                """
            )

    def _ensure_dataset_rows(self) -> None:
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO datasets (
                    id, user_id, name, slug, description, embedding_model, chunk_size, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    description = excluded.description,
                    embedding_model = excluded.embedding_model,
                    chunk_size = excluded.chunk_size,
                    updated_at = excluded.updated_at
                """,
                (
                    "dataset_default",
                    DEFAULT_USER_ID,
                    "Default Workspace",
                    "default",
                    "Your primary document knowledge base.",
                    DEFAULT_EMBEDDING_MODEL,
                    DEFAULT_CHUNK_SIZE,
                    now,
                    now,
                ),
            )

    def _ensure_seed_files(self) -> None:
        for dataset in SEED_DATASETS:
            dataset_dir = self._seed_root / _slugify(dataset["name"])
            dataset_dir.mkdir(parents=True, exist_ok=True)
            for document in dataset["documents"]:
                target = dataset_dir / document["file_name"]
                if not target.exists():
                    self._write_simple_pdf(
                        target,
                        document["title"],
                        dataset["name"],
                        document["content"],
                    )

    def list_datasets(self, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        self._ensure_dataset_rows()
        with self._connect() as connection:
            datasets = connection.execute(
                """
                SELECT
                    d.id,
                    d.name,
                    d.slug,
                    d.description,
                    d.embedding_model,
                    d.chunk_size,
                    COALESCE(doc_stats.document_count, 0) AS document_count,
                    COALESCE(doc_stats.ready_count, 0) AS ready_count,
                    COALESCE(doc_stats.processing_count, 0) AS processing_count,
                    COALESCE(doc_stats.failed_count, 0) AS failed_count,
                    COALESCE(chunk_stats.chunk_count, 0) AS chunk_count
                FROM datasets d
                LEFT JOIN (
                    SELECT
                        dataset_id,
                        COUNT(*) AS document_count,
                        SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready_count,
                        SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) AS processing_count,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
                    FROM documents
                    GROUP BY dataset_id
                ) AS doc_stats ON doc_stats.dataset_id = d.id
                LEFT JOIN (
                    SELECT dataset_id, COUNT(*) AS chunk_count
                    FROM chunks
                    GROUP BY dataset_id
                ) AS chunk_stats ON chunk_stats.dataset_id = d.id
                WHERE d.user_id = ?
                ORDER BY d.name
                """,
                (user_id,),
            ).fetchall()

            summary = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_datasets,
                    COALESCE((SELECT COUNT(*) FROM documents), 0) AS total_documents,
                    COALESCE((SELECT COUNT(*) FROM chunks), 0) AS total_chunks
                FROM datasets
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        return {
            "datasets": [dict(row) for row in datasets],
            "summary": dict(summary),
        }

    def list_documents(
        self,
        dataset_id: str,
        user_id: str = DEFAULT_USER_ID,
        page: int = 1,
        limit: int = 10,
    ) -> dict[str, Any]:
        dataset = self._get_dataset(dataset_id, user_id)
        page = max(1, page)
        limit = max(1, min(limit, 50))
        offset = (page - 1) * limit
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    doc.*,
                    COALESCE(COUNT(ch.id), 0) AS chunk_count
                FROM documents doc
                LEFT JOIN chunks ch ON ch.document_id = doc.id
                WHERE doc.dataset_id = ?
                GROUP BY doc.id
                ORDER BY doc.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (dataset_id, limit, offset),
            ).fetchall()
            total = connection.execute(
                "SELECT COUNT(*) AS total FROM documents WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()["total"]

        return {
            "dataset": dict(dataset),
            "page": page,
            "limit": limit,
            "total": total,
            "documents": [self._serialize_document(row) for row in rows],
        }

    def create_upload_record(
        self,
        dataset_id: str,
        file_name: str,
        content: bytes,
        mime_type: str,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict[str, Any]:
        dataset = self._get_dataset(dataset_id, user_id)
        if not file_name.lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported.")

        file_hash = hashlib.sha256(content).hexdigest()
        now = _utc_now()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM documents WHERE dataset_id = ? AND file_hash = ?",
                (dataset_id, file_hash),
            ).fetchone()
            if existing:
                return {
                    "document_id": existing["id"],
                    "dataset_id": dataset_id,
                    "file_name": existing["file_name"],
                    "status": existing["status"],
                    "duplicate": True,
                }

            document_id = f"doc_{uuid4().hex}"
            storage_dir = self._storage_root / dataset["slug"]
            storage_dir.mkdir(parents=True, exist_ok=True)
            safe_name = f"{uuid4().hex[:8]}-{file_name}"
            path = storage_dir / safe_name
            path.write_bytes(content)
            connection.execute(
                """
                INSERT INTO documents (
                    id, dataset_id, title, file_name, path, file_hash, mime_type, file_size, page_count,
                    status, error_message, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    dataset_id,
                    Path(file_name).stem,
                    file_name,
                    str(path),
                    file_hash,
                    mime_type or "application/pdf",
                    len(content),
                    0,
                    "processing",
                    None,
                    now,
                    now,
                ),
            )

        return {
            "document_id": document_id,
            "dataset_id": dataset_id,
            "file_name": file_name,
            "status": "processing",
            "duplicate": False,
        }

    def ingest_document(self, document_id: str) -> None:
        with self._connect() as connection:
            document = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        if not document:
            return

        file_path = Path(document["path"])
        parsed_pages: list[str] = []
        vectors_created = False
        try:
            parsed_pages = self._extract_pdf_pages(file_path)
            page_count = len(parsed_pages)
            chunks = self._build_chunks(document["dataset_id"], document_id, parsed_pages)
            embeddings = self._embed_chunks([chunk["text"] for chunk in chunks])
            self._ensure_qdrant_collection(
                len(embeddings[0]) if embeddings else embedding_service.vector_size()
            )
            for chunk, vector in zip(chunks, embeddings):
                chunk["embedding"] = vector

            self._replace_document_chunks(document_id, document["dataset_id"], chunks)
            self._upsert_qdrant_points(document["dataset_id"], document_id, chunks)
            vectors_created = True

            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE documents
                    SET status = 'ready', page_count = ?, error_message = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (page_count, _utc_now(), document_id),
                )
        except Exception as exc:
            self._cleanup_failed_ingestion(document_id, vectors_created)
            if len(parsed_pages) == 0 and file_path.exists():
                file_path.unlink(missing_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE documents
                    SET status = 'failed', error_message = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (str(exc), _utc_now(), document_id),
                )

    def seed_sample_corpus(self, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        self._ensure_dataset_rows()
        datasets_seeded = 0
        documents_seeded = 0
        chunks_indexed = 0

        for dataset in SEED_DATASETS:
            dataset_record = self._get_dataset(f"dataset_{_slugify(dataset['name'])}", user_id)
            datasets_seeded += 1
            seed_dir = self._seed_root / dataset_record["slug"]
            for seed_doc in dataset["documents"]:
                source = seed_dir / seed_doc["file_name"]
                upload_result = self.create_upload_record(
                    dataset_record["id"],
                    seed_doc["file_name"],
                    source.read_bytes(),
                    "application/pdf",
                    user_id=user_id,
                )
                if upload_result["duplicate"]:
                    continue
                documents_seeded += 1
                self.ingest_document(upload_result["document_id"])
                chunks_indexed += self._count_chunks(upload_result["document_id"])

        return {
            "datasets_seeded": datasets_seeded,
            "documents_seeded": documents_seeded,
            "chunks_indexed": chunks_indexed,
        }

    def delete_document(
        self,
        dataset_id: str,
        document_id: str,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict[str, Any]:
        document = self._get_document(dataset_id, document_id, user_id)
        removed_chunks = self._count_chunks(document_id)
        self._delete_qdrant_document(document_id)
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        Path(document["path"]).unlink(missing_ok=True)
        return {
            "document_id": document_id,
            "deleted": True,
            "removed_chunks": removed_chunks,
        }

    def get_document_file_path(
        self,
        dataset_id: str,
        document_id: str,
        user_id: str = DEFAULT_USER_ID,
    ) -> Path:
        document = self._get_document(dataset_id, document_id, user_id)
        return Path(document["path"])

    def query_dataset(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 5,
        user_id: str = DEFAULT_USER_ID,
    ) -> dict[str, Any]:
        self._get_dataset(dataset_id, user_id)
        normalized_query = " ".join(query.lower().split())
        cached = self._get_cached_query(dataset_id, normalized_query)
        if cached is not None:
            return {
                "dataset_id": dataset_id,
                "query": query,
                "cached": True,
                "results": cached,
            }

        embedding = self._embed_chunks([query])[0]
        results = self._search_qdrant(dataset_id, embedding, top_k)
        self._store_query_cache(dataset_id, normalized_query, results)
        return {
            "dataset_id": dataset_id,
            "query": query,
            "cached": False,
            "results": results,
        }

    def _serialize_document(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "dataset_id": row["dataset_id"],
            "title": row["title"],
            "file_name": row["file_name"],
            "mime_type": row["mime_type"],
            "file_size": row["file_size"],
            "page_count": row["page_count"],
            "status": row["status"],
            "error_message": row["error_message"],
            "chunk_count": row["chunk_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _get_dataset(self, dataset_id: str, user_id: str) -> sqlite3.Row:
        with self._connect() as connection:
            dataset = connection.execute(
                "SELECT * FROM datasets WHERE id = ? AND user_id = ?",
                (dataset_id, user_id),
            ).fetchone()
        if not dataset:
            raise ValueError("Dataset not found.")
        return dataset

    def _get_document(self, dataset_id: str, document_id: str, user_id: str) -> sqlite3.Row:
        dataset = self._get_dataset(dataset_id, user_id)
        with self._connect() as connection:
            document = connection.execute(
                "SELECT * FROM documents WHERE id = ? AND dataset_id = ?",
                (document_id, dataset["id"]),
            ).fetchone()
        if not document:
            raise ValueError("Document not found for this dataset.")
        return document

    def _count_chunks(self, document_id: str) -> int:
        with self._connect() as connection:
            return connection.execute(
                "SELECT COUNT(*) AS total FROM chunks WHERE document_id = ?",
                (document_id,),
            ).fetchone()["total"]

    def _extract_pdf_pages(self, file_path: Path) -> list[str]:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise KnowledgeBaseConfigError("pypdf is required for PDF ingestion.") from exc

        reader = PdfReader(str(file_path))
        return [(page.extract_text() or "").strip() for page in reader.pages]

    def _build_chunks(
        self,
        dataset_id: str,
        document_id: str,
        pages: list[str],
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        step = DEFAULT_CHUNK_SIZE - DEFAULT_CHUNK_OVERLAP
        for page_index, page_text in enumerate(pages, start=1):
            if not page_text:
                continue
            starts = [0] if len(page_text) <= DEFAULT_CHUNK_SIZE else list(range(0, len(page_text), step))
            for chunk_index, start in enumerate(starts):
                end = min(start + DEFAULT_CHUNK_SIZE, len(page_text))
                text = page_text[start:end].strip()
                if not text:
                    continue
                chunk_id = f"chunk_{uuid4().hex}"
                chunks.append(
                    {
                        "id": chunk_id,
                        "dataset_id": dataset_id,
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "page_number": page_index,
                        "start_char": start,
                        "end_char": end,
                        "text": text,
                        "vector_id": chunk_id,
                    }
                )
                if end >= len(page_text):
                    break

        return chunks

    def _embed_chunks(self, texts: list[str]) -> list[list[float]]:
        try:
            return embedding_service.embed_texts(texts)
        except RuntimeError as exc:
            raise KnowledgeBaseConfigError(str(exc)) from exc

    def _qdrant_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("QDRANT_API_KEY")
        if api_key:
            headers["api-key"] = api_key
        return headers

    def _qdrant_base_url(self) -> str:
        base_url = os.getenv("QDRANT_URL")
        if not base_url:
            raise KnowledgeBaseConfigError("QDRANT_URL is not configured.")
        return base_url.rstrip("/")

    def _qdrant_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> Any:
        request = urllib.request.Request(
            f"{self._qdrant_base_url()}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers=self._qdrant_headers(),
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                content = response.read()
                return json.loads(content.decode("utf-8")) if content else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and allow_404:
                return None
            detail = exc.read().decode("utf-8", errors="ignore")
            raise KnowledgeBaseConfigError(
                f"Qdrant request failed: {detail or exc.reason}"
            ) from exc

    def _ensure_qdrant_collection(self, vector_size: int) -> None:
        existing = self._qdrant_request(
            "GET",
            f"/collections/{self._collection}",
            allow_404=True,
        )
        if existing is None:
            self._qdrant_request(
                "PUT",
                f"/collections/{self._collection}",
                {"vectors": {"size": vector_size, "distance": "Cosine"}},
            )
            return

        existing_size = self._collection_vector_size(existing)
        if existing_size is not None and existing_size != vector_size:
            raise KnowledgeBaseConfigError(
                f"Qdrant collection '{self._collection}' uses vector size {existing_size}, expected {vector_size}. "
                "Use a new collection name for the local embedding pipeline."
            )

    def _collection_vector_size(self, response: dict[str, Any]) -> int | None:
        vectors = (
            response.get("result", {})
            .get("config", {})
            .get("params", {})
            .get("vectors")
        )
        if isinstance(vectors, dict):
            size = vectors.get("size")
            if isinstance(size, int):
                return size
        return None

    def _upsert_qdrant_points(
        self,
        dataset_id: str,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> None:
        self._qdrant_request(
            "PUT",
            f"/collections/{self._collection}/points?wait=true",
            {
                "points": [
                    {
                        "id": chunk["vector_id"],
                        "vector": chunk["embedding"],
                        "payload": {
                            "dataset_id": dataset_id,
                            "document_id": document_id,
                            "chunk_id": chunk["id"],
                            "text": chunk["text"],
                            "page": chunk["page_number"],
                            "chunk_index": chunk["chunk_index"],
                            "start_char": chunk["start_char"],
                            "end_char": chunk["end_char"],
                        },
                    }
                    for chunk in chunks
                ]
            },
        )

    def _replace_document_chunks(
        self,
        document_id: str,
        dataset_id: str,
        chunks: list[dict[str, Any]],
    ) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, dataset_id, chunk_index, page_number, start_char, end_char, text, vector_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk["id"],
                        document_id,
                        dataset_id,
                        chunk["chunk_index"],
                        chunk["page_number"],
                        chunk["start_char"],
                        chunk["end_char"],
                        chunk["text"],
                        chunk["vector_id"],
                        _utc_now(),
                    )
                    for chunk in chunks
                ],
            )

    def _delete_qdrant_document(self, document_id: str) -> None:
        try:
            self._qdrant_request(
                "POST",
                f"/collections/{self._collection}/points/delete?wait=true",
                {
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": document_id},
                            }
                        ]
                    }
                },
            )
        except KnowledgeBaseConfigError:
            return

    def _cleanup_failed_ingestion(self, document_id: str, vectors_created: bool) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        if vectors_created:
            self._delete_qdrant_document(document_id)

    def _store_query_cache(
        self,
        dataset_id: str,
        normalized_query: str,
        results: list[dict[str, Any]],
    ) -> None:
        now = datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO query_cache (
                    id, dataset_id, query_hash, query_text, response_json, created_at, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dataset_id, query_hash) DO UPDATE SET
                    response_json = excluded.response_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (
                    f"cache_{uuid4().hex}",
                    dataset_id,
                    hashlib.sha256(normalized_query.encode("utf-8")).hexdigest(),
                    normalized_query,
                    json.dumps(results),
                    now.isoformat(),
                    (now + timedelta(hours=1)).isoformat(),
                ),
            )

    def _get_cached_query(
        self,
        dataset_id: str,
        normalized_query: str,
    ) -> list[dict[str, Any]] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT response_json, expires_at
                FROM query_cache
                WHERE dataset_id = ? AND query_hash = ?
                """,
                (
                    dataset_id,
                    hashlib.sha256(normalized_query.encode("utf-8")).hexdigest(),
                ),
            ).fetchone()
        if not row:
            return None
        if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
            return None
        return json.loads(row["response_json"])

    def _search_qdrant(
        self,
        dataset_id: str,
        vector: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        result = self._qdrant_request(
            "POST",
            f"/collections/{self._collection}/points/search",
            {
                "vector": vector,
                "limit": top_k,
                "with_payload": True,
                "filter": {
                    "must": [
                        {
                            "key": "dataset_id",
                            "match": {"value": dataset_id},
                        }
                    ]
                },
            },
        )
        payloads = result.get("result", [])
        titles = self._document_titles_for_results(payloads)
        return [
            {
                "chunk_id": item["payload"]["chunk_id"],
                "document_id": item["payload"]["document_id"],
                "document_title": titles.get(item["payload"]["document_id"], "Document"),
                "page_number": item["payload"]["page"],
                "start_char": item["payload"]["start_char"],
                "end_char": item["payload"]["end_char"],
                "text": item["payload"]["text"],
                "score": item["score"],
            }
            for item in payloads
        ]

    def _document_titles_for_results(self, payloads: list[dict[str, Any]]) -> dict[str, str]:
        doc_ids = {
            item["payload"]["document_id"]
            for item in payloads
            if item.get("payload", {}).get("document_id")
        }
        if not doc_ids:
            return {}
        placeholders = ",".join("?" for _ in doc_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT id, title FROM documents WHERE id IN ({placeholders})",
                tuple(doc_ids),
            ).fetchall()
        return {row["id"]: row["title"] for row in rows}

    def _write_simple_pdf(
        self,
        target: Path,
        title: str,
        dataset_name: str,
        lines: list[str],
    ) -> None:
        try:
            from fpdf import FPDF
        except ImportError as exc:
            raise KnowledgeBaseConfigError("fpdf2 is required for seeding real PDFs. Please run `pip install fpdf2`") from exc

        pdf = FPDF()
        pdf.add_page()
        
        # Add a professional header
        pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_font("helvetica", "I", 14)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, f"Domain: {dataset_name}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        
        # Add contents
        pdf.set_font("helvetica", "", 12)
        pdf.set_text_color(20, 20, 20)
        for line in lines:
            pdf.multi_cell(0, 8, line)
            pdf.ln(5)
            
        pdf.output(str(target))


knowledge_base_service = KnowledgeBaseService()
