from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_WORKSPACE_ID = "demo-workspace"
DEFAULT_USER_ID = "demo-user"


class PauseIteration(Exception):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__("Workflow is waiting for human approval.")
        self.payload = payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


NODE_TYPES: list[dict[str, Any]] = [
    {
        "type": "trigger_webhook",
        "family": "trigger",
        "label": "Webhook Trigger",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"path": "/webhooks/new"},
    },
    {
        "type": "trigger_schedule",
        "family": "trigger",
        "label": "Schedule Trigger",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"cron": "0 * * * *"},
    },
    {
        "type": "transform",
        "family": "core",
        "label": "Transform",
        "supports_ai_brain": True,
        "supports_memory": False,
        "default_config": {"template": "{{input}}"},
    },
    {
        "type": "condition",
        "family": "core",
        "label": "Condition",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"expression": "True"},
    },
    {
        "type": "delay",
        "family": "core",
        "label": "Delay",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"seconds": 1},
    },
    {
        "type": "loop",
        "family": "core",
        "label": "Loop",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"items_path": "items"},
    },
    {
        "type": "sub_workflow",
        "family": "core",
        "label": "Sub Workflow",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"workflow_id": ""},
    },
    {
        "type": "llm_generate",
        "family": "ai",
        "label": "LLM Generate",
        "supports_ai_brain": True,
        "supports_memory": True,
        "default_config": {
            "prompt": "Summarize the input",
            "memory": "short_term",
        },
    },
    {
        "type": "llm_classify",
        "family": "ai",
        "label": "LLM Classify",
        "supports_ai_brain": True,
        "supports_memory": True,
        "default_config": {
            "prompt": "Classify the input",
            "memory": "short_term",
        },
    },
    {
        "type": "llm_decision",
        "family": "ai",
        "label": "LLM Decision",
        "supports_ai_brain": True,
        "supports_memory": True,
        "default_config": {
            "prompt": "Decide next action",
            "memory": "short_term",
        },
    },
    {
        "type": "human_approval",
        "family": "human",
        "label": "Human Approval",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"message": "Approve this step?"},
    },
    {
        "type": "integration_slack",
        "family": "integration",
        "label": "Slack Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "send_message"},
    },
    {
        "type": "integration_notion",
        "family": "integration",
        "label": "Notion Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "create_page"},
    },
    {
        "type": "integration_stripe",
        "family": "integration",
        "label": "Stripe Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "create_payment_link"},
    },
    {
        "type": "integration_gmail",
        "family": "integration",
        "label": "Gmail Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "send_email"},
    },
    {
        "type": "integration_google_sheets",
        "family": "integration",
        "label": "Google Sheets Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "append_row"},
    },
    {
        "type": "integration_hubspot",
        "family": "integration",
        "label": "HubSpot Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "create_contact"},
    },
    {
        "type": "integration_github",
        "family": "integration",
        "label": "GitHub Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "create_issue"},
    },
    {
        "type": "integration_zendesk",
        "family": "integration",
        "label": "Zendesk Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "create_ticket"},
    },
    {
        "type": "integration_qdrant",
        "family": "integration",
        "label": "Qdrant Search",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "search_vectors"},
    },
    {
        "type": "integration_twitter",
        "family": "integration",
        "label": "Twitter Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "publish_post"},
    },
    {
        "type": "integration_linkedin",
        "family": "integration",
        "label": "LinkedIn Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "publish_post"},
    },
    {
        "type": "integration_document_parser",
        "family": "integration",
        "label": "Document Parser",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "parse_document"},
    },
    {
        "type": "integration_accounting",
        "family": "integration",
        "label": "Accounting Action",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "create_entry"},
    },
    {
        "type": "integration_sentry",
        "family": "integration",
        "label": "Sentry Trigger",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "new_alert"},
    },
    {
        "type": "integration_log_fetch",
        "family": "integration",
        "label": "Log Fetch",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "fetch_logs"},
    },
    {
        "type": "integration_shopify",
        "family": "integration",
        "label": "Shopify Trigger",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "new_order"},
    },
    {
        "type": "integration_inventory",
        "family": "integration",
        "label": "Inventory Check",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "check_stock"},
    },
    {
        "type": "integration_enrichment_api",
        "family": "integration",
        "label": "Enrichment API",
        "supports_ai_brain": False,
        "supports_memory": False,
        "default_config": {"action": "enrich"},
    },
]


def _node(
    node_id: str,
    node_type: str,
    name: str,
    x: int,
    y: int,
    config: dict[str, Any] | None = None,
    ai_brain: bool = False,
    memory: str | None = None,
    timeout_ms: int = 10000,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": node_type,
        "name": name,
        "position": {"x": x, "y": y},
        "config": config or {},
        "ai_brain": ai_brain,
        "memory": memory,
        "retry_policy": {
            "max_retries": 2,
            "backoff": "exponential",
            "retry_on": ["timeout", "api_error"],
        },
        "timeout_ms": timeout_ms,
    }


def _edge(edge_id: str, source: str, target: str, condition: str = "true") -> dict[str, Any]:
    return {"id": edge_id, "source": source, "target": target, "condition": condition}


TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "tpl_ai_customer_support",
        "name": "AI Customer Support Agent (Multi-channel)",
        "category": "Operations",
        "difficulty": "advanced",
        "description": "Classifies inbound support requests and auto-replies simple cases while escalating complex ones.",
        "integrations_required": ["gmail", "zendesk", "slack"],
        "nodes": [
            _node("n1", "integration_gmail", "Gmail Trigger", 80, 180, {"action": "new_message"}),
            _node("n2", "llm_classify", "Intent + Sentiment", 340, 180, {"prompt": "Classify support intent and sentiment."}, True, "short_term", 30000),
            _node("n3", "condition", "Simple Request?", 600, 180, {"expression": "True"}),
            _node("n4", "llm_generate", "Generate Reply", 860, 100, {"prompt": "Draft a concise support reply."}, True, "short_term", 30000),
            _node("n5", "integration_zendesk", "Create Zendesk Ticket", 860, 260, {"action": "create_ticket"}),
            _node("n6", "integration_slack", "Notify Human Team", 1120, 260, {"action": "send_message"}),
        ],
        "edges": [
            _edge("e1", "n1", "n2"),
            _edge("e2", "n2", "n3"),
            _edge("e3", "n3", "n4", "result.get('result') == True"),
            _edge("e4", "n3", "n5", "result.get('result') == False"),
            _edge("e5", "n5", "n6"),
        ],
    },
    {
        "id": "tpl_fraud_detection_payment_review",
        "name": "Fraud Detection & Payment Review System",
        "category": "Risk",
        "difficulty": "advanced",
        "description": "Scores payment risk and routes suspicious transactions through human approval.",
        "integrations_required": ["stripe", "slack"],
        "nodes": [
            _node("n1", "integration_stripe", "Stripe Payment Trigger", 80, 180, {"action": "payment_received"}),
            _node("n2", "llm_decision", "LLM Risk Scoring", 340, 180, {"prompt": "Score payment risk from 0 to 1 with explanation."}, True, "short_term", 30000),
            _node("n3", "condition", "Risk > Threshold", 600, 180, {"expression": "True"}),
            _node("n4", "integration_slack", "Alert Fraud Channel", 860, 120, {"action": "send_message"}),
            _node("n5", "human_approval", "Human Payment Review", 1120, 120, {"message": "Approve flagged payment?"}),
        ],
        "edges": [
            _edge("e1", "n1", "n2"),
            _edge("e2", "n2", "n3"),
            _edge("e3", "n3", "n4", "result.get('result') == True"),
            _edge("e4", "n4", "n5"),
        ],
    },
    {
        "id": "tpl_ai_lead_qualification",
        "name": "AI Lead Qualification + CRM Routing",
        "category": "Sales",
        "difficulty": "advanced",
        "description": "Enriches inbound leads, scores quality, and routes qualified leads to CRM and sales alerts.",
        "integrations_required": ["hubspot", "slack"],
        "nodes": [
            _node("n1", "trigger_webhook", "Lead Form Trigger", 80, 180, {"path": "/webhooks/new-lead"}),
            _node("n2", "integration_enrichment_api", "Lead Enrichment API", 340, 180, {"action": "enrich"}),
            _node("n3", "llm_classify", "Lead Quality Scoring", 600, 180, {"prompt": "Score lead quality and summarize fit."}, True, "short_term", 30000),
            _node("n4", "condition", "Qualified Lead?", 860, 180, {"expression": "True"}),
            _node("n5", "integration_hubspot", "Update HubSpot", 1120, 120, {"action": "create_or_update_contact"}),
            _node("n6", "integration_slack", "Notify Sales Team", 1120, 260, {"action": "send_message"}),
        ],
        "edges": [
            _edge("e1", "n1", "n2"),
            _edge("e2", "n2", "n3"),
            _edge("e3", "n3", "n4"),
            _edge("e4", "n4", "n5", "result.get('result') == True"),
            _edge("e5", "n5", "n6"),
        ],
    },
    {
        "id": "tpl_rag_internal_knowledge_assistant",
        "name": "RAG-based Internal Knowledge Assistant",
        "category": "AI",
        "difficulty": "advanced",
        "description": "Accepts user queries, retrieves relevant knowledge chunks, and responds with context-aware answers.",
        "integrations_required": ["qdrant"],
        "nodes": [
            _node("n1", "trigger_webhook", "Chat Query Input", 80, 180, {"path": "/webhooks/internal-kb-query"}),
            _node("n2", "integration_qdrant", "Vector Search (Qdrant)", 340, 180, {"action": "search_vectors"}),
            _node("n3", "llm_generate", "Generate Contextual Answer", 600, 180, {"prompt": "Answer using retrieved context only."}, True, "dataset_ref", 30000),
            _node("n4", "transform", "Return Response", 860, 180, {"template": "{{input}}"}),
        ],
        "edges": [_edge("e1", "n1", "n2"), _edge("e2", "n2", "n3"), _edge("e3", "n3", "n4")],
    },
    {
        "id": "tpl_social_media_content_engine",
        "name": "AI Social Media Content Engine",
        "category": "Marketing",
        "difficulty": "medium",
        "description": "Generates daily social content, transforms copy per platform, and auto-posts to channels.",
        "integrations_required": ["twitter", "linkedin"],
        "nodes": [
            _node("n1", "trigger_schedule", "Daily Scheduler", 80, 180, {"cron": "0 9 * * *"}),
            _node("n2", "llm_generate", "Generate Content Draft", 340, 180, {"prompt": "Write social media copy for today."}, True, "short_term", 30000),
            _node("n3", "transform", "Adapt per Platform", 600, 180, {"template": "{{input}}"}),
            _node("n4", "integration_twitter", "Post to Twitter", 860, 120, {"action": "publish_post"}),
            _node("n5", "integration_linkedin", "Post to LinkedIn", 860, 260, {"action": "publish_post"}),
        ],
        "edges": [_edge("e1", "n1", "n2"), _edge("e2", "n2", "n3"), _edge("e3", "n3", "n4"), _edge("e4", "n3", "n5")],
    },
    {
        "id": "tpl_smart_invoice_processing",
        "name": "Smart Invoice Processing & Approval",
        "category": "Finance",
        "difficulty": "advanced",
        "description": "Parses uploaded invoices, validates extracted fields with AI, and routes approved entries to accounting.",
        "integrations_required": ["accounting"],
        "nodes": [
            _node("n1", "trigger_webhook", "Invoice Upload", 80, 180, {"path": "/webhooks/invoice-upload"}),
            _node("n2", "integration_document_parser", "OCR / Parser", 340, 180, {"action": "extract_fields"}),
            _node("n3", "llm_decision", "LLM Validation", 600, 180, {"prompt": "Validate invoice fields and flag issues."}, True, "short_term", 30000),
            _node("n4", "condition", "Valid Invoice?", 860, 180, {"expression": "True"}),
            _node("n5", "human_approval", "Finance Approval", 1120, 120, {"message": "Approve invoice for posting?"}),
            _node("n6", "integration_accounting", "Accounting Update", 1380, 120, {"action": "create_entry"}),
        ],
        "edges": [
            _edge("e1", "n1", "n2"),
            _edge("e2", "n2", "n3"),
            _edge("e3", "n3", "n4"),
            _edge("e4", "n4", "n5", "result.get('result') == True"),
            _edge("e5", "n5", "n6"),
        ],
    },
    {
        "id": "tpl_devops_incident_copilot",
        "name": "DevOps Incident Response Copilot",
        "category": "Engineering",
        "difficulty": "advanced",
        "description": "Analyzes incident alerts, summarizes probable root causes, and opens action items for engineers.",
        "integrations_required": ["sentry", "slack", "github"],
        "nodes": [
            _node("n1", "integration_sentry", "Sentry Trigger", 80, 180, {"action": "new_alert"}),
            _node("n2", "integration_log_fetch", "Fetch Logs", 340, 180, {"action": "fetch_logs"}),
            _node("n3", "llm_generate", "LLM Incident Analysis", 600, 180, {"prompt": "Analyze incident logs and suggest fixes."}, True, "short_term", 30000),
            _node("n4", "integration_slack", "Notify Incident Channel", 860, 120, {"action": "send_message"}),
            _node("n5", "integration_github", "Create GitHub Issue", 860, 260, {"action": "create_issue"}),
        ],
        "edges": [_edge("e1", "n1", "n2"), _edge("e2", "n2", "n3"), _edge("e3", "n3", "n4"), _edge("e4", "n3", "n5")],
    },
    {
        "id": "tpl_ecommerce_order_manager",
        "name": "E-commerce Smart Order Manager",
        "category": "Commerce",
        "difficulty": "advanced",
        "description": "Evaluates incoming orders for stock, fraud risk, and fulfillment priority with AI-assisted branching.",
        "integrations_required": ["shopify", "slack", "gmail"],
        "nodes": [
            _node("n1", "integration_shopify", "Shopify Order Trigger", 80, 180, {"action": "new_order"}),
            _node("n2", "integration_inventory", "Inventory Check", 340, 180, {"action": "check_stock"}),
            _node("n3", "llm_decision", "LLM Priority Decision", 600, 180, {"prompt": "Determine fulfillment priority and fraud confidence."}, True, "short_term", 30000),
            _node("n4", "condition", "Priority Fulfillment?", 860, 180, {"expression": "True"}),
            _node("n5", "integration_gmail", "Notify by Email", 1120, 120, {"action": "send_email"}),
            _node("n6", "integration_slack", "Notify Ops Slack", 1120, 260, {"action": "send_message"}),
        ],
        "edges": [
            _edge("e1", "n1", "n2"),
            _edge("e2", "n2", "n3"),
            _edge("e3", "n3", "n4"),
            _edge("e4", "n4", "n5", "result.get('result') == True"),
            _edge("e5", "n4", "n6", "result.get('result') == False"),
        ],
    },
    {
        "id": "tpl_meeting_notes_to_tasks",
        "name": "AI Meeting Notes -> Task Automation",
        "category": "Productivity",
        "difficulty": "medium",
        "description": "Converts meeting transcripts into actionable task lists and publishes assignments to collaboration tools.",
        "integrations_required": ["notion", "slack"],
        "nodes": [
            _node("n1", "trigger_webhook", "Transcript Input", 80, 180, {"path": "/webhooks/meeting-transcript"}),
            _node("n2", "llm_generate", "Meeting Summary", 340, 180, {"prompt": "Summarize key meeting outcomes."}, True, "short_term", 30000),
            _node("n3", "llm_classify", "Task Extraction", 600, 180, {"prompt": "Extract tasks, owners, and due dates."}, True, "short_term", 30000),
            _node("n4", "integration_notion", "Create Notion Tasks", 860, 120, {"action": "create_page"}),
            _node("n5", "integration_slack", "Notify Task Owners", 860, 260, {"action": "send_message"}),
        ],
        "edges": [_edge("e1", "n1", "n2"), _edge("e2", "n2", "n3"), _edge("e3", "n3", "n4"), _edge("e4", "n3", "n5")],
    },
    {
        "id": "tpl_multistep_approval_engine",
        "name": "Multi-step Approval Workflow Engine",
        "category": "Governance",
        "difficulty": "advanced",
        "description": "Scores request priority with AI and routes the request through sequential approval stages before final action.",
        "integrations_required": ["slack"],
        "nodes": [
            _node("n1", "trigger_webhook", "Request Trigger", 80, 180, {"path": "/webhooks/approval-request"}),
            _node("n2", "llm_decision", "Priority Scoring", 340, 180, {"prompt": "Score request urgency and business impact."}, True, "short_term", 30000),
            _node("n3", "human_approval", "Manager Approval", 600, 120, {"message": "Manager approval required."}),
            _node("n4", "human_approval", "Director Approval", 860, 120, {"message": "Director approval required."}),
            _node("n5", "condition", "Final Decision", 1120, 120, {"expression": "True"}),
            _node("n6", "integration_slack", "Final Action Notify", 1380, 120, {"action": "send_message"}),
        ],
        "edges": [
            _edge("e1", "n1", "n2"),
            _edge("e2", "n2", "n3"),
            _edge("e3", "n3", "n4"),
            _edge("e4", "n4", "n5"),
            _edge("e5", "n5", "n6", "result.get('result') == True"),
        ],
    },
]


class WorkflowPlatformService:
    def __init__(self) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self._db_path = backend_root / "data" / "workflow_platform.sqlite3"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()
        self._seed_templates()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    draft_snapshot TEXT NOT NULL,
                    published_version_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    updated_by TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflow_versions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    json_snapshot TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    UNIQUE(workflow_id, version_number)
                );

                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    workflow_version_id TEXT,
                    workspace_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    debug INTEGER NOT NULL DEFAULT 0,
                    parent_run_id TEXT,
                    status TEXT NOT NULL,
                    initial_input TEXT NOT NULL,
                    context_snapshot TEXT NOT NULL,
                    final_output TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workflow_steps (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    node_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    input_snapshot TEXT NOT NULL,
                    output_snapshot TEXT,
                    decision_snapshot TEXT,
                    error_message TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS approval_tasks (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_snapshot TEXT NOT NULL,
                    decision TEXT,
                    decided_by TEXT,
                    created_at TEXT NOT NULL,
                    decided_at TEXT
                );

                CREATE TABLE IF NOT EXISTS llm_usage (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    run_id TEXT,
                    node_id TEXT,
                    model TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    cost REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    description TEXT NOT NULL,
                    integrations_required TEXT NOT NULL,
                    workflow_snapshot TEXT NOT NULL
                );
                """
            )

    def _seed_templates(self) -> None:
        with self._connect() as connection:
            existing_rows = connection.execute(
                "SELECT id, name FROM templates ORDER BY id"
            ).fetchall()
            expected_names = [template["name"] for template in TEMPLATES]
            existing_names = [row["name"] for row in existing_rows]
            if len(existing_rows) == len(TEMPLATES) and set(existing_names) == set(expected_names):
                return

            connection.execute("DELETE FROM templates")
            for template in TEMPLATES:
                workflow_snapshot = {
                    "name": template["name"],
                    "nodes": template["nodes"],
                    "edges": template["edges"],
                }
                connection.execute(
                    """
                    INSERT INTO templates (
                        id, name, category, difficulty, description, integrations_required, workflow_snapshot
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        template["id"],
                        template["name"],
                        template["category"],
                        template["difficulty"],
                        template["description"],
                        json.dumps(template["integrations_required"]),
                        json.dumps(workflow_snapshot),
                    ),
                )

    def list_workflows(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    w.*,
                    (
                        SELECT MAX(version_number) FROM workflow_versions v WHERE v.workflow_id = w.id
                    ) AS latest_version,
                    (
                        SELECT COUNT(*) FROM workflow_runs r WHERE r.workflow_id = w.id
                    ) AS run_count
                FROM workflows w
                ORDER BY w.updated_at DESC
                """
            ).fetchall()
        workflows: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["draft_snapshot"] = json.loads(item["draft_snapshot"])
            item["versions"] = []
            workflows.append(item)
        return workflows

    def create_workflow(self, name: str, snapshot: dict[str, Any], user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        workflow_id = f"wf_{uuid4().hex}"
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflows (
                    id, workspace_id, name, status, draft_snapshot, published_version_id,
                    created_at, updated_at, created_by, updated_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow_id,
                    DEFAULT_WORKSPACE_ID,
                    name,
                    "draft",
                    json.dumps(snapshot),
                    None,
                    now,
                    now,
                    user_id,
                    user_id,
                ),
            )
        return self.get_workflow(workflow_id)

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            workflow = connection.execute(
                "SELECT * FROM workflows WHERE id = ?",
                (workflow_id,),
            ).fetchone()
            if not workflow:
                raise ValueError("Workflow not found.")
            versions = connection.execute(
                """
                SELECT id, version_number, created_at, created_by
                FROM workflow_versions
                WHERE workflow_id = ?
                ORDER BY version_number DESC
                """,
                (workflow_id,),
            ).fetchall()
        payload = dict(workflow)
        payload["draft_snapshot"] = json.loads(payload["draft_snapshot"])
        payload["versions"] = [dict(row) for row in versions]
        return payload

    def update_workflow(self, workflow_id: str, name: str, snapshot: dict[str, Any], user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        self.validate_snapshot(snapshot)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE workflows
                SET name = ?, draft_snapshot = ?, updated_at = ?, updated_by = ?
                WHERE id = ?
                """,
                (name, json.dumps(snapshot), _utc_now(), user_id, workflow_id),
            )
        return self.get_workflow(workflow_id)

    def validate_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        nodes = snapshot.get("nodes", [])
        edges = snapshot.get("edges", [])
        node_ids = {node.get("id") for node in nodes}
        if not nodes:
            raise ValueError("Workflow must include at least one node.")
        for edge in edges:
            if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
                raise ValueError("Edges must connect valid nodes.")
            if edge.get("condition") is None:
                raise ValueError("Every edge must define a condition.")
        self._detect_cycles(nodes, edges)
        return {"valid": True, "nodes": len(nodes), "edges": len(edges)}

    def publish_workflow(self, workflow_id: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        snapshot = workflow["draft_snapshot"]
        self.validate_snapshot(snapshot)
        with self._connect() as connection:
            latest = connection.execute(
                "SELECT COALESCE(MAX(version_number), 0) AS latest FROM workflow_versions WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()["latest"]
            version_id = f"wfv_{uuid4().hex}"
            connection.execute(
                """
                INSERT INTO workflow_versions (
                    id, workflow_id, version_number, json_snapshot, created_at, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    workflow_id,
                    latest + 1,
                    json.dumps(snapshot),
                    _utc_now(),
                    user_id,
                ),
            )
            connection.execute(
                """
                UPDATE workflows
                SET status = 'published', published_version_id = ?, updated_at = ?, updated_by = ?
                WHERE id = ?
                """,
                (version_id, _utc_now(), user_id, workflow_id),
            )
        return self.get_workflow(workflow_id)

    def rollback_workflow(self, workflow_id: str, version_id: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        with self._connect() as connection:
            version = connection.execute(
                "SELECT json_snapshot FROM workflow_versions WHERE workflow_id = ? AND id = ?",
                (workflow_id, version_id),
            ).fetchone()
            if not version:
                raise ValueError("Version not found.")
            connection.execute(
                """
                UPDATE workflows
                SET status = 'draft', draft_snapshot = ?, updated_at = ?, updated_by = ?
                WHERE id = ?
                """,
                (version["json_snapshot"], _utc_now(), user_id, workflow_id),
            )
        return self.get_workflow(workflow_id)

    def list_versions(self, workflow_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, workflow_id, version_number, created_at, created_by
                FROM workflow_versions
                WHERE workflow_id = ?
                ORDER BY version_number DESC
                """,
                (workflow_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_node_types(self) -> list[dict[str, Any]]:
        return NODE_TYPES

    def list_templates(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM templates ORDER BY id").fetchall()
        templates: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["integrations_required"] = json.loads(item["integrations_required"])
            item["workflow_snapshot"] = json.loads(item["workflow_snapshot"])
            templates.append(item)
        return templates

    def instantiate_template(self, template_id: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM templates WHERE id = ?",
                (template_id,),
            ).fetchone()
        if not row:
            raise ValueError("Template not found.")
        template = dict(row)
        return self.create_workflow(
            name=template["name"],
            snapshot=json.loads(template["workflow_snapshot"]),
            user_id=user_id,
        )

    def list_runs(self, workflow_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM workflow_runs
                WHERE workflow_id = ?
                ORDER BY created_at DESC
                """,
                (workflow_id,),
            ).fetchall()
        return [self._deserialize_run(row) for row in rows]

    def get_run(self, workflow_id: str, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            run = connection.execute(
                "SELECT * FROM workflow_runs WHERE workflow_id = ? AND id = ?",
                (workflow_id, run_id),
            ).fetchone()
            if not run:
                raise ValueError("Run not found.")
            steps = connection.execute(
                """
                SELECT *
                FROM workflow_steps
                WHERE run_id = ?
                ORDER BY started_at ASC
                """,
                (run_id,),
            ).fetchall()
        payload = self._deserialize_run(run)
        payload["steps"] = [self._deserialize_step(step) for step in steps]
        return payload

    def list_approvals(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM approval_tasks ORDER BY created_at DESC"
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload_snapshot"] = json.loads(item["payload_snapshot"])
            result.append(item)
        return result

    def decide_approval(self, approval_id: str, decision: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        if decision not in {"approve", "reject"}:
            raise ValueError("Decision must be approve or reject.")
        with self._connect() as connection:
            approval = connection.execute(
                "SELECT * FROM approval_tasks WHERE id = ?",
                (approval_id,),
            ).fetchone()
            if not approval:
                raise ValueError("Approval task not found.")
            connection.execute(
                """
                UPDATE approval_tasks
                SET status = ?, decision = ?, decided_by = ?, decided_at = ?
                WHERE id = ?
                """,
                ("resolved", decision, user_id, _utc_now(), approval_id),
            )
            updated = connection.execute(
                "SELECT * FROM approval_tasks WHERE id = ?",
                (approval_id,),
            ).fetchone()
        if not updated:
            raise ValueError("Approval task not found after update.")
        result = dict(updated)
        result["payload_snapshot"] = json.loads(result["payload_snapshot"])
        return result

    def get_llm_usage(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM llm_usage ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def run_workflow(
        self,
        workflow_id: str,
        mode: str,
        debug: bool = False,
        input_data: dict[str, Any] | None = None,
        version_id: str | None = None,
        parent_run_id: str | None = None,
    ) -> dict[str, Any]:
        if mode not in {"manual", "trigger", "test"}:
            raise ValueError("Invalid execution mode.")

        workflow = self.get_workflow(workflow_id)
        snapshot, workflow_version_id = self._resolve_snapshot_for_run(workflow, mode, version_id)
        run_id = f"run_{uuid4().hex}"
        context = {
            "input": input_data or {},
            "node_outputs": {},
            "global_vars": {
                "mode": mode,
                "workflow_id": workflow_id,
                "debug": debug,
            },
        }
        now = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_runs (
                    id, workflow_id, workflow_version_id, workspace_id, mode, debug, parent_run_id,
                    status, initial_input, context_snapshot, final_output, error_message, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    workflow_id,
                    workflow_version_id,
                    DEFAULT_WORKSPACE_ID,
                    mode,
                    1 if debug else 0,
                    parent_run_id,
                    "running",
                    json.dumps(context["input"]),
                    json.dumps(context),
                    None,
                    None,
                    now,
                    now,
                ),
            )

        try:
            final_output = self._execute_snapshot(run_id, workflow_id, snapshot, context, mode, debug)
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE workflow_runs
                    SET status = ?, final_output = ?, context_snapshot = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("completed", json.dumps(final_output), json.dumps(context), _utc_now(), run_id),
                )
        except PauseIteration as paused:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE workflow_runs
                    SET status = ?, context_snapshot = ?, final_output = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("waiting_approval", json.dumps(context), json.dumps(paused.payload), _utc_now(), run_id),
                )
        except Exception as exc:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE workflow_runs
                    SET status = ?, error_message = ?, context_snapshot = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("failed", str(exc), json.dumps(context), _utc_now(), run_id),
                )

        return self.get_run(workflow_id, run_id)

    def _resolve_snapshot_for_run(
        self,
        workflow: dict[str, Any],
        mode: str,
        version_id: str | None,
    ) -> tuple[dict[str, Any], str | None]:
        if version_id:
            with self._connect() as connection:
                version = connection.execute(
                    "SELECT * FROM workflow_versions WHERE workflow_id = ? AND id = ?",
                    (workflow["id"], version_id),
                ).fetchone()
            if not version:
                raise ValueError("Requested workflow version was not found.")
            return json.loads(version["json_snapshot"]), version["id"]

        if mode == "test":
            return workflow["draft_snapshot"], None

        published_id = workflow["published_version_id"]
        if not published_id:
            raise ValueError("Workflow must be published before manual or trigger runs.")

        with self._connect() as connection:
            version = connection.execute(
                "SELECT * FROM workflow_versions WHERE id = ?",
                (published_id,),
            ).fetchone()
        return json.loads(version["json_snapshot"]), published_id

    def _execute_snapshot(
        self,
        run_id: str,
        workflow_id: str,
        snapshot: dict[str, Any],
        context: dict[str, Any],
        mode: str,
        debug: bool,
    ) -> dict[str, Any]:
        nodes = {node["id"]: node for node in snapshot.get("nodes", [])}
        edges = snapshot.get("edges", [])
        incoming = {node_id: [] for node_id in nodes}
        outgoing = {node_id: [] for node_id in nodes}
        for edge in edges:
            incoming[edge["target"]].append(edge)
            outgoing[edge["source"]].append(edge)

        queue = [node_id for node_id, parents in incoming.items() if not parents]
        processed: set[str] = set()
        final_output: dict[str, Any] = {}

        while queue:
            node_id = queue.pop(0)
            if node_id in processed:
                continue
            node = nodes[node_id]
            node_input = self._resolve_node_input(node_id, incoming[node_id], context)
            result = self._execute_node(run_id, workflow_id, node, node_input, context, mode, debug)
            if result is not None:
                context["node_outputs"][node_id] = result
                final_output = result if isinstance(result, dict) else {"value": result}

            processed.add(node_id)
            for edge in outgoing[node_id]:
                if self._edge_allows(edge, result, context):
                    queue.append(edge["target"])

        return final_output

    def _resolve_node_input(
        self,
        node_id: str,
        incoming_edges: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        if not incoming_edges:
            return context["input"]
        payloads = []
        for edge in incoming_edges:
            source = edge["source"]
            if source in context["node_outputs"]:
                payloads.append(context["node_outputs"][source])
        return {
            "input": context["input"],
            "upstream": payloads,
            "global_vars": context["global_vars"],
        }

    def _edge_allows(
        self,
        edge: dict[str, Any],
        node_result: Any,
        context: dict[str, Any],
    ) -> bool:
        condition = str(edge.get("condition", "true")).strip()
        if condition == "true":
            return True
        if condition == "false":
            return False
        scope = {
            "result": node_result,
            "input": context["input"],
            "node_outputs": context["node_outputs"],
            "global_vars": context["global_vars"],
        }
        return bool(eval(condition, {"__builtins__": {}}, scope))

    def _execute_node(
        self,
        run_id: str,
        workflow_id: str,
        node: dict[str, Any],
        node_input: dict[str, Any],
        context: dict[str, Any],
        mode: str,
        debug: bool,
    ) -> Any:
        retry_policy = node.get("retry_policy") or {
            "max_retries": 0,
            "backoff": "none",
            "retry_on": [],
        }
        max_retries = retry_policy.get("max_retries", 0)
        attempt = 0
        last_error: Exception | None = None
        while attempt <= max_retries:
            attempt += 1
            step_id = f"step_{uuid4().hex}"
            started_at = _utc_now()
            decision_snapshot = None
            try:
                if node.get("ai_brain"):
                    decision_snapshot = self._run_ai_brain(node, node_input, context)
                    if decision_snapshot["action"] == "skip":
                        self._write_step(
                            step_id, run_id, node, "skipped", attempt, node_input, None, decision_snapshot, None, started_at
                        )
                        return None
                    if decision_snapshot["action"] == "modify_input":
                        node_input = decision_snapshot["modified_input"]

                result = self._execute_node_by_type(
                    run_id, workflow_id, node, node_input, context, mode, debug
                )
                self._write_step(
                    step_id, run_id, node, "completed", attempt, node_input, result, decision_snapshot, None, started_at
                )
                return result
            except PauseIteration:
                self._write_step(
                    step_id, run_id, node, "waiting_approval", attempt, node_input, None, decision_snapshot, None, started_at
                )
                raise
            except Exception as exc:
                last_error = exc
                self._write_step(
                    step_id, run_id, node, "failed", attempt, node_input, None, decision_snapshot, str(exc), started_at
                )
                if attempt > max_retries:
                    raise
                if retry_policy.get("backoff") == "exponential":
                    time.sleep(min(2 ** (attempt - 1), 4))
        if last_error:
            raise last_error
        return None

    def _execute_node_by_type(
        self,
        run_id: str,
        workflow_id: str,
        node: dict[str, Any],
        node_input: dict[str, Any],
        context: dict[str, Any],
        mode: str,
        debug: bool,
    ) -> Any:
        node_type = node["type"]
        config = node.get("config", {})
        if node_type in {"trigger_webhook", "trigger_schedule"}:
            return node_input
        if node_type == "transform":
            template = str(config.get("template", "{{input}}"))
            return {
                "transformed": template.replace("{{input}}", json.dumps(node_input)),
                "source": node_input,
            }
        if node_type == "condition":
            expression = config.get("expression", "True")
            scope = {
                "input": node_input,
                "node_outputs": context["node_outputs"],
                "global_vars": context["global_vars"],
            }
            return {"result": bool(eval(expression, {"__builtins__": {}}, scope))}
        if node_type == "delay":
            seconds = min(float(config.get("seconds", 1)), 5.0)
            time.sleep(seconds)
            return {"delayed": seconds, "input": node_input}
        if node_type == "loop":
            items_path = str(config.get("items_path", "items"))
            items = []
            if isinstance(node_input, dict):
                items = node_input.get(items_path, []) or node_input.get("items", [])
            return {"items": list(items), "count": len(items)}
        if node_type == "human_approval":
            approval_id = f"approval_{uuid4().hex}"
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO approval_tasks (
                        id, workflow_id, run_id, node_id, workspace_id, message, status, payload_snapshot,
                        decision, decided_by, created_at, decided_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        approval_id,
                        workflow_id,
                        run_id,
                        node["id"],
                        DEFAULT_WORKSPACE_ID,
                        config.get("message", "Approve this step?"),
                        "pending",
                        json.dumps(node_input),
                        None,
                        None,
                        _utc_now(),
                        None,
                    ),
                )
            raise PauseIteration({"approval_id": approval_id, "message": config.get("message", "Approve this step?")})
        if node_type == "sub_workflow":
            child_workflow_id = config.get("workflow_id")
            if not child_workflow_id:
                raise ValueError("Sub-workflow node requires workflow_id.")
            child_run = self.run_workflow(
                child_workflow_id,
                mode=mode if mode != "trigger" else "manual",
                debug=debug,
                input_data={"from_parent": workflow_id, "payload": node_input},
                parent_run_id=run_id,
            )
            return {"sub_workflow_run_id": child_run["id"], "status": child_run["status"]}
        if node_type.startswith("integration_"):
            return {
                "integration": node_type.replace("integration_", ""),
                "action": config.get("action", "execute"),
                "input": node_input,
                "status": "accepted",
            }
        if node_type in {"llm_generate", "llm_classify", "llm_decision"}:
            memory_mode = node.get("memory") or config.get("memory") or "short_term"
            prompt = config.get("prompt", "Process this input.")
            llm_response = self._call_llm(prompt, node_input, memory_mode)
            self._record_llm_usage(run_id, node["id"], llm_response["model"], llm_response["tokens_used"], llm_response["cost"])
            return llm_response
        raise ValueError(f"Unsupported node type: {node_type}")

    def _run_ai_brain(
        self,
        node: dict[str, Any],
        node_input: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        if node["type"] == "condition":
            return {"action": "continue"}
        if isinstance(node_input, dict) and node_input.get("skip"):
            return {"action": "skip"}
        return {"action": "continue"}

    def _call_llm(
        self,
        prompt: str,
        node_input: dict[str, Any],
        memory_mode: str,
    ) -> dict[str, Any]:
        provider = self._route_llm(prompt, node_input)
        if provider == "gemini":
            text = self._call_gemini(prompt, node_input, memory_mode)
            model = "gemini-2.0-flash"
        else:
            text = self._call_openai(prompt, node_input, memory_mode)
            model = "gpt-4.1-mini"
        tokens_used = max(32, len(prompt) + len(json.dumps(node_input)))
        return {
            "model": model,
            "provider": provider,
            "memory": memory_mode,
            "text": text,
            "tokens_used": tokens_used,
            "cost": round(tokens_used * 0.000002, 6),
        }

    def _route_llm(self, prompt: str, node_input: dict[str, Any]) -> str:
        complexity = len(prompt.split()) + len(json.dumps(node_input))
        return "gemini" if complexity > 500 else "openai"

    def _call_openai(self, prompt: str, node_input: dict[str, Any], memory_mode: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        payload = {
            "model": os.getenv("OPENAI_WORKFLOW_MODEL", "gpt-4.1-mini"),
            "messages": [
                {"role": "system", "content": f"You are AuraFlow. Memory mode: {memory_mode}."},
                {"role": "user", "content": f"{prompt}\n\nInput:\n{json.dumps(node_input)}"},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]

    def _call_gemini(self, prompt: str, node_input: dict[str, Any], memory_mode: str) -> str:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured.")
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Memory mode: {memory_mode}\n{prompt}\nInput:\n{json.dumps(node_input)}"
                        }
                    ]
                }
            ]
        }
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["candidates"][0]["content"]["parts"][0]["text"]

    def _record_llm_usage(
        self,
        run_id: str,
        node_id: str,
        model: str,
        tokens_used: int,
        cost: float,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO llm_usage (
                    id, workspace_id, run_id, node_id, model, tokens_used, cost, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"usage_{uuid4().hex}",
                    DEFAULT_WORKSPACE_ID,
                    run_id,
                    node_id,
                    model,
                    tokens_used,
                    cost,
                    _utc_now(),
                ),
            )

    def _write_step(
        self,
        step_id: str,
        run_id: str,
        node: dict[str, Any],
        status: str,
        attempt: int,
        input_snapshot: Any,
        output_snapshot: Any,
        decision_snapshot: Any,
        error_message: str | None,
        started_at: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO workflow_steps (
                    id, run_id, node_id, node_type, status, attempt, input_snapshot, output_snapshot,
                    decision_snapshot, error_message, started_at, finished_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    run_id,
                    node["id"],
                    node["type"],
                    status,
                    attempt,
                    json.dumps(input_snapshot),
                    json.dumps(output_snapshot) if output_snapshot is not None else None,
                    json.dumps(decision_snapshot) if decision_snapshot is not None else None,
                    error_message,
                    started_at,
                    _utc_now(),
                ),
            )

    def _deserialize_run(self, row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["initial_input"] = json.loads(payload["initial_input"])
        payload["context_snapshot"] = json.loads(payload["context_snapshot"])
        payload["final_output"] = json.loads(payload["final_output"]) if payload["final_output"] else None
        return payload

    def _deserialize_step(self, row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["input_snapshot"] = json.loads(payload["input_snapshot"])
        payload["output_snapshot"] = json.loads(payload["output_snapshot"]) if payload["output_snapshot"] else None
        payload["decision_snapshot"] = json.loads(payload["decision_snapshot"]) if payload["decision_snapshot"] else None
        return payload

    def _detect_cycles(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
        adjacency = {node["id"]: [] for node in nodes}
        for edge in edges:
            adjacency[edge["source"]].append(edge["target"])
        visited: set[str] = set()
        active: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in active:
                raise ValueError("Workflow graph contains a cycle.")
            if node_id in visited:
                return
            active.add(node_id)
            for next_id in adjacency[node_id]:
                visit(next_id)
            active.remove(node_id)
            visited.add(node_id)

        for node in nodes:
            visit(node["id"])


workflow_platform_service = WorkflowPlatformService()
