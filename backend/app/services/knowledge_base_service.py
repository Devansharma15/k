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


DEFAULT_USER_ID = "demo-user"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
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


SEED_DATASETS = [
    {
        "name": "Education",
        "description": "Curriculum, assessment, and learning operations.",
        "documents": [
            {
                "title": "Instructional Design Notes",
                "file_name": "instructional-design-notes.pdf",
                "content": [
                    "Instructional design aligns learning outcomes, activities, and assessment methods.",
                    "Effective curricula scaffold complexity while keeping feedback loops short and useful.",
                    "Learning experiences benefit from clarity, repetition, and examples tied to authentic tasks.",
                    "Well-structured materials improve student confidence and reduce avoidable confusion.",
                ],
            },
            {
                "title": "Assessment Strategy Guide",
                "file_name": "assessment-strategy-guide.pdf",
                "content": [
                    "Assessment strategies should measure knowledge, reasoning, and application rather than recall alone.",
                    "Rubrics help create transparent expectations and support consistent grading.",
                    "Frequent low-stakes checks give instructors faster signal about learner progress.",
                    "Program reviews should connect assessment evidence to curriculum improvement plans.",
                ],
            },
        ],
    },
    {
        "name": "Research Papers",
        "description": "Paper reading, synthesis, and scientific communication.",
        "documents": [
            {
                "title": "Reading Scientific Papers",
                "file_name": "reading-scientific-papers.pdf",
                "content": [
                    "Reading scientific papers effectively starts with the abstract, figures, and conclusion.",
                    "Researchers then inspect methods, assumptions, baselines, and evaluation choices in detail.",
                    "A strong reading habit captures open questions, reproducibility notes, and related work.",
                    "Paper libraries are more useful when summaries and tags are maintained consistently.",
                ],
            },
            {
                "title": "Literature Review Framework",
                "file_name": "literature-review-framework.pdf",
                "content": [
                    "Literature reviews organize prior work by theme, method, gap, and evidence strength.",
                    "A useful review explains where the field agrees, where uncertainty remains, and why.",
                    "Researchers should note sampling limitations, datasets, evaluation metrics, and confounders.",
                    "A good synthesis supports better experimental design and clearer positioning.",
                ],
            },
        ],
    },
    {
        "name": "Programming",
        "description": "Software engineering, systems design, and code quality.",
        "documents": [
            {
                "title": "Software Design Patterns",
                "file_name": "software-design-patterns.pdf",
                "content": [
                    "Design patterns provide reusable ways to organize behavior, state, and communication.",
                    "Patterns should support clarity and maintainability rather than become ceremony.",
                    "Teams often combine modular boundaries, typed interfaces, and observability primitives.",
                    "Strong design practice includes careful tradeoffs around coupling, testing, and failure recovery.",
                ],
            },
            {
                "title": "Code Review Playbook",
                "file_name": "code-review-playbook.pdf",
                "content": [
                    "Code review focuses first on correctness, regression risk, and missing test coverage.",
                    "Helpful feedback explains impact and suggests paths forward without obscuring ownership.",
                    "Review quality improves when changes are small, well-described, and easy to exercise.",
                    "A healthy review culture balances product speed with long-term system health.",
                ],
            },
        ],
    },
    {
        "name": "Business",
        "description": "Strategy, operations, decision-making, and execution.",
        "documents": [
            {
                "title": "Business Strategy Overview",
                "file_name": "business-strategy-overview.pdf",
                "content": [
                    "Business strategy aligns market position, differentiation, operations, and resource allocation.",
                    "Leaders identify where the company can win and what capabilities are required to do so.",
                    "Execution improves when strategic choices are visible in roadmaps, staffing, and metrics.",
                    "Teams need feedback loops that connect customer signal to planning decisions.",
                ],
            },
            {
                "title": "Operating Rhythm Guide",
                "file_name": "operating-rhythm-guide.pdf",
                "content": [
                    "Operating rhythm includes planning cadences, reviews, escalation paths, and decision forums.",
                    "Clear accountability and shared metrics reduce cross-functional friction.",
                    "Well-run organizations maintain a small number of meaningful goals and check progress often.",
                    "A strong rhythm supports speed without losing alignment or execution quality.",
                ],
            },
        ],
    },
    {
        "name": "Marketing",
        "description": "Audience insight, campaigns, messaging, and measurement.",
        "documents": [
            {
                "title": "Campaign Planning Guide",
                "file_name": "campaign-planning-guide.pdf",
                "content": [
                    "Campaign planning begins with audience definition, message clarity, and measurable outcomes.",
                    "Marketers align channels, creative, timing, and budget to a consistent narrative.",
                    "Campaign reviews compare conversion quality, CAC, retention, and funnel bottlenecks.",
                    "Strong planning reduces waste and improves iteration speed across channels.",
                ],
            },
            {
                "title": "Brand Messaging Framework",
                "file_name": "brand-messaging-framework.pdf",
                "content": [
                    "Brand messaging turns customer pain points into a consistent point of view.",
                    "Effective messaging is concrete, differentiated, and easy to repeat across teams.",
                    "Positioning should be tested with prospects, internal teams, and performance data.",
                    "A durable message architecture improves launch quality and sales enablement.",
                ],
            },
        ],
    },
    {
        "name": "E-commerce",
        "description": "Catalog, fulfillment, merchandising, and conversion operations.",
        "documents": [
            {
                "title": "E-commerce Operations Handbook",
                "file_name": "ecommerce-operations-handbook.pdf",
                "content": [
                    "E-commerce operations coordinate catalog quality, pricing, inventory, fulfillment, and support.",
                    "High-performing stores reduce friction in search, checkout, shipping, and returns.",
                    "Teams monitor conversion, average order value, repeat purchase rate, and margin.",
                    "Operational resilience matters during launches, promotions, and seasonal demand spikes.",
                ],
            },
            {
                "title": "Merchandising and Conversion Notes",
                "file_name": "merchandising-and-conversion-notes.pdf",
                "content": [
                    "Merchandising combines assortment, presentation, and merchandising rules to guide purchase intent.",
                    "Good product pages answer common objections with clarity, trust, and rich evidence.",
                    "Experimentation helps teams learn which offers, bundles, and layouts increase conversion.",
                    "Insights from returns and support can improve the storefront as much as paid acquisition.",
                ],
            },
        ],
    },
    {
        "name": "Psychology",
        "description": "Behavior, cognition, and mental processes.",
        "documents": [
            {
                "title": "Cognitive Biases Survey",
                "file_name": "cognitive-biases-survey.pdf",
                "content": [
                    "Cognitive biases influence judgment under uncertainty, stress, and limited attention.",
                    "Common examples include anchoring, confirmation bias, and availability effects.",
                    "Decision support systems can reduce bias when they surface alternatives and missing data.",
                    "Teams benefit from structured reflection when making high-stakes decisions.",
                ],
            },
            {
                "title": "Motivation and Behavior Notes",
                "file_name": "motivation-and-behavior-notes.pdf",
                "content": [
                    "Motivation research examines intrinsic drivers, rewards, context, and habit formation.",
                    "Behavior change usually requires small loops of cue, action, and reinforcement.",
                    "Organizations can improve outcomes by designing systems that support autonomy and mastery.",
                    "Useful interventions balance clarity, accountability, and realistic pacing.",
                ],
            },
        ],
    },
    {
        "name": "History",
        "description": "Historical method, sources, and long-term change.",
        "documents": [
            {
                "title": "Historical Analysis Primer",
                "file_name": "historical-analysis-primer.pdf",
                "content": [
                    "Historical analysis compares sources, context, chronology, and competing interpretations.",
                    "Primary evidence should be read with attention to authorship, audience, and purpose.",
                    "Historians examine continuity and change across institutions, technology, and culture.",
                    "Good historical writing connects evidence to argument without overstating certainty.",
                ],
            },
            {
                "title": "Archives and Sources Guide",
                "file_name": "archives-and-sources-guide.pdf",
                "content": [
                    "Archives preserve letters, reports, photographs, and records that support historical inquiry.",
                    "Researchers document provenance carefully to avoid citation errors and weak claims.",
                    "Source triangulation helps assess bias, reliability, and missing viewpoints.",
                    "A disciplined notes system makes synthesis and writing much easier later on.",
                ],
            },
        ],
    },
    {
        "name": "Environment",
        "description": "Climate, ecosystems, policy, and sustainability.",
        "documents": [
            {
                "title": "Climate Systems Overview",
                "file_name": "climate-systems-overview.pdf",
                "content": [
                    "Climate systems involve atmospheric circulation, oceans, biospheres, and human activity.",
                    "Environmental analysis often connects emissions, land use, resilience, and adaptation planning.",
                    "Effective sustainability programs rely on measurable targets and transparent reporting.",
                    "Decision-makers need both local context and long-range scenarios to plan responsibly.",
                ],
            },
            {
                "title": "Sustainability Reporting Notes",
                "file_name": "sustainability-reporting-notes.pdf",
                "content": [
                    "Sustainability reports track emissions, water, waste, energy, and supply chain practices.",
                    "Data quality is critical because environmental claims require evidence and consistency.",
                    "Many organizations align reports to shared frameworks for comparability and governance.",
                    "Cross-functional ownership improves both reporting quality and operational follow-through.",
                ],
            },
        ],
    },
    {
        "name": "Cybersecurity",
        "description": "Threat detection, controls, response, and resilience.",
        "documents": [
            {
                "title": "Security Operations Brief",
                "file_name": "security-operations-brief.pdf",
                "content": [
                    "Security operations monitor identity, endpoints, logs, and alerts for suspicious activity.",
                    "Incident response depends on preparation, triage quality, and communication discipline.",
                    "Detection engineering improves when controls are reviewed against realistic attacker paths.",
                    "A strong security posture combines technical controls with practiced operational response.",
                ],
            },
            {
                "title": "Application Security Checklist",
                "file_name": "application-security-checklist.pdf",
                "content": [
                    "Application security includes secure defaults, dependency review, secrets handling, and testing.",
                    "Teams should prioritize auth flows, data access, input handling, and observability.",
                    "Threat modeling helps identify likely abuse cases before they reach production.",
                    "Security reviews are most effective when they are early, repeatable, and actionable.",
                ],
            },
        ],
    },
    {
        "name": "AI & Machine Learning",
        "description": "Foundational concepts and practical applications across AI systems.",
        "documents": [
            {
                "title": "Neural Networks Overview",
                "file_name": "neural-networks-overview.pdf",
                "content": [
                    "Neural networks are layered function approximators designed to map inputs to outputs.",
                    "Training usually involves gradient descent, backpropagation, and careful regularization.",
                    "Modern machine learning systems rely on embeddings, transformers, retrieval, and evaluation.",
                    "Production AI systems must also consider latency, observability, and safe failure modes.",
                ],
            },
            {
                "title": "Retrieval Augmented Generation Basics",
                "file_name": "retrieval-augmented-generation-basics.pdf",
                "content": [
                    "Retrieval augmented generation combines document search with generative models.",
                    "A typical pipeline extracts text, chunks documents, embeds chunks, and stores vectors.",
                    "At query time the system embeds the question, retrieves relevant chunks, and synthesizes an answer.",
                    "Good RAG quality depends on document hygiene, chunk design, metadata, and evaluation.",
                ],
            },
        ],
    },
    {
        "name": "Data Science",
        "description": "Statistics, experimentation, pipelines, and analytical workflows.",
        "documents": [
            {
                "title": "Data Cleaning Handbook",
                "file_name": "data-cleaning-handbook.pdf",
                "content": [
                    "Data cleaning includes schema checks, null handling, deduplication, and distribution review.",
                    "Feature quality often matters more than model complexity in business analytics projects.",
                    "A clean analytical pipeline documents assumptions, transformations, and validation rules.",
                    "Teams should monitor data freshness and guard against silent upstream drift.",
                ],
            },
            {
                "title": "Experiment Design Primer",
                "file_name": "experiment-design-primer.pdf",
                "content": [
                    "Experiment design starts with a hypothesis, an outcome metric, and a clear sampling plan.",
                    "Randomization reduces bias while power analysis helps avoid under-sized tests.",
                    "Analysts should report effect sizes, confidence intervals, and practical implications.",
                    "A reliable experimentation practice also tracks guardrail metrics and logging quality.",
                ],
            },
        ],
    },
    {
        "name": "Healthcare",
        "description": "Clinical workflows, patient safety, and healthcare operations.",
        "documents": [
            {
                "title": "Clinical Documentation Guide",
                "file_name": "clinical-documentation-guide.pdf",
                "content": [
                    "Clinical documentation must be timely, legible, attributable, and useful at the point of care.",
                    "Structured notes improve downstream coding, care coordination, and patient follow-up.",
                    "Healthcare systems rely on careful access control, auditability, and decision support.",
                    "Documentation quality directly affects patient safety and continuity of care.",
                ],
            },
            {
                "title": "Hospital Operations Summary",
                "file_name": "hospital-operations-summary.pdf",
                "content": [
                    "Hospital operations coordinate staffing, triage, scheduling, supply flow, and discharge planning.",
                    "Bottlenecks often appear in emergency departments, imaging, and bed assignment workflows.",
                    "Operational dashboards help teams monitor throughput, occupancy, and incident response.",
                    "Reliable escalation policies reduce delays in treatment and improve patient experience.",
                ],
            },
        ],
    },
    {
        "name": "Finance",
        "description": "Financial controls, reporting, risk, and market structure.",
        "documents": [
            {
                "title": "Corporate Finance Fundamentals",
                "file_name": "corporate-finance-fundamentals.pdf",
                "content": [
                    "Corporate finance evaluates capital allocation, financing choices, and long-term value creation.",
                    "Core topics include cash flow, discount rates, working capital, and profitability.",
                    "Financial reporting depends on reliable controls, consistent periods, and reconciled ledgers.",
                    "Leaders balance growth opportunities against liquidity, debt, and operational risk.",
                ],
            },
            {
                "title": "Risk Controls Overview",
                "file_name": "risk-controls-overview.pdf",
                "content": [
                    "Risk controls include segregation of duties, transaction monitoring, and exception review.",
                    "Audit trails and reconciliations help organizations detect fraud and reporting issues early.",
                    "Treasury workflows often monitor cash positions, exposure, and funding obligations daily.",
                    "Operational resilience matters as much as forecasting accuracy in financial systems.",
                ],
            },
        ],
    },
    {
        "name": "Legal",
        "description": "Contracts, compliance, legal process, and document review.",
        "documents": [
            {
                "title": "Contract Review Checklist",
                "file_name": "contract-review-checklist.pdf",
                "content": [
                    "Contract review checks definitions, obligations, payment terms, liability, and termination clauses.",
                    "Teams should confirm governing law, confidentiality language, and assignment provisions.",
                    "Clear issue spotting prevents downstream disputes and reduces negotiation cycles.",
                    "Version control and approval records are important for enterprise legal operations.",
                ],
            },
            {
                "title": "Compliance Monitoring Notes",
                "file_name": "compliance-monitoring-notes.pdf",
                "content": [
                    "Compliance teams maintain policies, evidence registers, incident logs, and control testing records.",
                    "Monitoring programs benefit from recurring review cadences and clearly named owners.",
                    "When obligations change, organizations need fast impact assessment across systems and vendors.",
                    "A well-run compliance function reduces operational risk and strengthens audit readiness.",
                ],
            },
        ],
    },
]


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
        self._collection = os.getenv("QDRANT_COLLECTION", "auraflow_knowledge_base")
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
            for dataset in SEED_DATASETS:
                slug = _slugify(dataset["name"])
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
                        f"dataset_{slug}",
                        DEFAULT_USER_ID,
                        dataset["name"],
                        slug,
                        dataset["description"],
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
            self._ensure_qdrant_collection(len(embeddings[0]) if embeddings else 1536)
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
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise KnowledgeBaseConfigError("OPENAI_API_KEY is not configured.")

        model = os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        embeddings: list[list[float]] = []
        for index in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[index : index + EMBEDDING_BATCH_SIZE]
            payload = json.dumps({"model": model, "input": batch}).encode("utf-8")
            request = urllib.request.Request(
                "https://api.openai.com/v1/embeddings",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    body = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                raise KnowledgeBaseConfigError(
                    f"OpenAI embedding request failed: {detail or exc.reason}"
                ) from exc
            embeddings.extend(item["embedding"] for item in body["data"])
        return embeddings

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
        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        content_lines = [
            "BT",
            "/F1 20 Tf",
            "50 760 Td",
            f"({escape(title)}) Tj",
            "0 -26 Td",
            "/F1 12 Tf",
            f"({escape(dataset_name)}) Tj",
        ]
        for line in lines:
            content_lines.extend(["0 -20 Td", f"({escape(line)}) Tj"])
        content_lines.append("ET")
        stream = "\n".join(content_lines)
        objects = [
            "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
            "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
            f"5 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream\nendobj\n",
        ]
        output = "%PDF-1.4\n"
        offsets = [0]
        for obj in objects:
            offsets.append(len(output.encode("utf-8")))
            output += obj
        xref_offset = len(output.encode("utf-8"))
        output += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for offset in offsets[1:]:
            output += f"{offset:010d} 00000 n \n"
        output += (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        )
        target.write_bytes(output.encode("utf-8"))


knowledge_base_service = KnowledgeBaseService()
