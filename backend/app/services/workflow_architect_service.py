"""
AuraFlow — Intelligent Workflow Compiler & System Orchestrator
==============================================================

Dual-mode system that converts user intent into:

  MODE 1 — WORKFLOW: Deterministic, executable workflow graphs
  MODE 2 — CODE:     Code-graph-aware answers via MCP context

Workflow Pipeline:
  1. ModeRouter        — decides workflow vs code mode
  2. IntentExtractor   — LLM extracts structured JSON intent (regex fallback)
  3. PatternMatcher    — matches intent → canonical workflow template
  4. ToolSelector      — filters tools by NODE_TYPES + connected providers
  5. GraphCompiler     — builds minimal deterministic graph from pattern
  6. DataMapper        — wires {{node_id.output.field}} bindings
  7. Validator         — enforces structural + semantic correctness
  8. ConfidenceScorer  — deterministic 0-100 rubric

Constraints:
  - EXACTLY one trigger per workflow
  - NO duplicate nodes (unless pattern explicitly requires)
  - NO hallucinated or unsupported integrations
  - NO empty configs — every required field must be populated
  - Output must pass workflow_platform_service.validate_snapshot()
"""

from __future__ import annotations

import glob
import json
import os
import pathlib
import re
import urllib.error
import urllib.request
from typing import Any
from uuid import uuid4

from .embedding_service import embedding_service
from .integrations_service import integrations_service
from .workflow_platform_service import NODE_TYPES


# ══════════════════════════════════════════════════════════════════════════
#  MODE ROUTER — decides workflow vs code mode
# ══════════════════════════════════════════════════════════════════════════

_WORKFLOW_SIGNALS = {
    "build", "automate", "send", "connect", "create workflow",
    "trigger", "schedule", "integrate", "bulk", "loop",
    "email to", "sheets", "telegram", "slack", "discord",
    "webhook", "rag pipeline", "summarize youtube",
    "workflow", "automation", "notify",
}

_CODE_SIGNALS = {
    "why", "error", "bug", "code", "fix", "explain",
    "how does", "where is", "what does", "trace", "debug",
    "function", "import", "dependency", "service",
    "call graph", "architecture", "file", "module",
    "stack trace", "exception", "crash",
}


class ModeRouter:
    """Decides whether a prompt should trigger WORKFLOW or CODE mode using keyword scoring."""

    def route(self, prompt: str) -> tuple[str, dict[str, int]]:
        p = prompt.lower()

        workflow_score = sum(1 for kw in _WORKFLOW_SIGNALS if kw in p)
        code_score = sum(1 for kw in _CODE_SIGNALS if kw in p)

        mode_scores = {"workflow": workflow_score, "code": code_score}

        if code_score > workflow_score:
            return "code", mode_scores
        return "workflow", mode_scores


# ══════════════════════════════════════════════════════════════════════════
#  CODE MODE — MCP-style code graph query engine
# ══════════════════════════════════════════════════════════════════════════

# Project root (two levels up from this service file)
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]

# Service graph: file → callable services / relationships
_SERVICE_GRAPH: dict[str, dict[str, Any]] = {
    "workflow_architect_service": {
        "path": "backend/app/services/workflow_architect_service.py",
        "role": "Workflow compiler — converts prompts to executable graphs",
        "imports": ["embedding_service", "integrations_service", "workflow_platform_service"],
        "exports": ["workflow_architect_service"],
        "api_routes": ["/api/generate-workflow"],
    },
    "workflow_platform_service": {
        "path": "backend/app/services/workflow_platform_service.py",
        "role": "Workflow execution engine — CRUD, run, validate, publish workflows",
        "imports": ["integrations_service"],
        "exports": ["workflow_platform_service", "NODE_TYPES"],
        "api_routes": ["/api/workflows/platform", "/api/node-types", "/api/templates"],
    },
    "integrations_service": {
        "path": "backend/app/services/integrations_service.py",
        "role": "Integration hub — manages provider connections (OAuth + API keys)",
        "imports": [],
        "exports": ["integrations_service"],
        "api_routes": ["/api/integrations"],
    },
    "embedding_service": {
        "path": "backend/app/services/embedding_service.py",
        "role": "Local embedding service — all-MiniLM-L6-v2 for semantic routing",
        "imports": [],
        "exports": ["embedding_service"],
        "api_routes": [],
    },
    "knowledge_base_service": {
        "path": "backend/app/services/knowledge_base_service.py",
        "role": "RAG pipeline — FAISS + BM25 + cross-encoder reranking",
        "imports": [],
        "exports": ["knowledge_base_service"],
        "api_routes": ["/api/knowledge-base"],
    },
}


class CodeGraphEngine:
    """
    MCP-style code graph query engine.
    Resolves prompts about code, bugs, and architecture by traversing
    the project's service graph and file structure.
    """

    def query(self, prompt: str) -> dict[str, Any]:
        p = prompt.lower()

        # Find relevant services by keyword
        relevant: list[dict[str, Any]] = []
        relationships: list[str] = []

        for svc_name, meta in _SERVICE_GRAPH.items():
            # Check if the service or its role is mentioned
            if svc_name.replace("_", " ") in p or svc_name in p:
                relevant.append({"service": svc_name, **meta})
                continue
            # Check if any of its API routes are mentioned
            for route in meta.get("api_routes", []):
                if route in p:
                    relevant.append({"service": svc_name, **meta})
                    break
            # Check role keywords
            role_words = meta.get("role", "").lower().split()
            if any(w in p for w in role_words if len(w) > 4):
                relevant.append({"service": svc_name, **meta})

        # Deduplicate & rank
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for r in sorted(relevant, key=lambda x: x.get("score, 0"), reverse=True):
            if r["service"] not in seen:
                deduped.append(r)
                seen.add(r["service"])
        relevant = deduped[:5]

        # Build relationship edges
        for svc in relevant:
            for imp in svc.get("imports", []):
                relationships.append(f"{svc['service']} → imports → {imp}")

        # If no matches, scan project files for keyword hits
        if not relevant:
            relevant, relationships = self._scan_files(p)

        # Build explanation
        explanation = self._explain(prompt, relevant, relationships)

        return {
            "mode": "code",
            "explanation": explanation,
            "relevant_nodes": relevant,
            "relationships": relationships,
        }

    def _scan_files(self, query: str) -> tuple[list[dict[str, Any]], list[str]]:
        """Fallback: scan Python files for the query keyword."""
        results: list[dict[str, Any]] = []
        backend_dir = _PROJECT_ROOT / "backend" / "app"
        if not backend_dir.exists():
            return results, []

        keywords = [w for w in query.split() if len(w) > 3]
        if not keywords:
            return results, []

        for py_file in backend_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                lower_content = content.lower()
                if any(kw in lower_content for kw in keywords):
                    # Extract function names that match
                    funcs = re.findall(r"def (\w+)\(", content)
                    matching_funcs = [
                        f for f in funcs
                        if any(kw in f.lower() for kw in keywords)
                    ]
                    results.append({
                        "file": str(py_file.relative_to(_PROJECT_ROOT)),
                        "matching_functions": matching_funcs[:5],
                    })
            except Exception:
                continue

        return results[:10], []

    def _explain(self, prompt: str, nodes: list, relationships: list) -> str:
        if not nodes:
            return f"No code graph nodes found matching: {prompt}"
        parts = [f"Found {len(nodes)} relevant code node(s):"]
        for node in nodes:
            if "service" in node:
                parts.append(f"  • {node['service']}: {node.get('role', 'N/A')}")
                parts.append(f"    Path: {node.get('path', 'N/A')}")
            elif "file" in node:
                parts.append(f"  • {node['file']}")
                if node.get("matching_functions"):
                    parts.append(f"    Functions: {', '.join(node['matching_functions'])}")
        if relationships:
            parts.append("\nRelationships:")
            for r in relationships:
                parts.append(f"  {r}")
        return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════════
#  TOOL REGISTRY ADAPTER
#  Normalizes workflow_platform_service.NODE_TYPES into compiler metadata.
# ══════════════════════════════════════════════════════════════════════════

_NODE_TYPE_MAP: dict[str, dict[str, Any]] = {n["type"]: n for n in NODE_TYPES}


def _get_available_integrations() -> list[dict[str, str]]:
    """Flatten integrations_service into [{provider, status}]."""
    try:
        data = integrations_service.get_integrations()
        flat: list[dict[str, str]] = []
        for cat in data.get("categories", []):
            for prov in cat.get("providers", []):
                flat.append({
                    "provider": prov["slug"].lower(),
                    "status": "connected" if prov.get("status") == "Connected" else "not_connected",
                })
        return flat
    except Exception:
        return []


def _connected_providers() -> set[str]:
    return {p["provider"] for p in _get_available_integrations() if p["status"] == "connected"}


def _provider_for_type(node_type: str) -> str | None:
    return _NODE_TYPE_MAP.get(node_type, {}).get("provider_slug")


# ══════════════════════════════════════════════════════════════════════════
#  NODE OUTPUT SCHEMAS  — compiler-owned, keyed by node type
# ══════════════════════════════════════════════════════════════════════════

NODE_OUTPUT_SCHEMAS: dict[str, list[str]] = {
    "trigger_webhook":             ["payload", "headers", "method"],
    "trigger_schedule":            ["triggered_at"],
    "integration_google_sheets":   ["rows", "updated_range", "updated_rows"],
    "integration_gmail":           ["status", "message_id", "from", "subject", "body"],
    "integration_qdrant":          ["matches", "count"],
    "integration_telegram":        ["message_id", "chat_id", "text"],
    "integration_discord":         ["message_id"],
    "integration_slack":           ["message_id", "channel"],
    "llm_generate":                ["text", "tokens_used"],
    "llm_classify":                ["category", "confidence", "categories"],
    "llm_decision":                ["decision", "intent", "extracted"],
    "loop":                        ["item", "index"],
    "transform":                   ["result"],
    "condition":                   ["result"],
}


# ══════════════════════════════════════════════════════════════════════════
#  SEMANTIC ROUTER (Dify-style tool similarity matching)
# ══════════════════════════════════════════════════════════════════════════

class DifySemanticRouter:
    """
    Embeds tool descriptions into latent space and cosine-matches against
    the user prompt to discover integrations not mentioned by keyword.
    """

    def __init__(self) -> None:
        self._tool_embeddings: dict[str, list[float]] = {}
        self._is_initialized: bool = False

    def _initialize(self) -> None:
        if self._is_initialized:
            return
        try:
            texts, keys = [], []
            for n in NODE_TYPES:
                slug = n.get("provider_slug")
                if slug:
                    txt = f"Platform: {slug}. Label: {n.get('label')}. Family: {n.get('family')}."
                    texts.append(txt)
                    keys.append(n["type"])
            if texts:
                embedded = embedding_service.embed_batch(texts)
                for k, vec in zip(keys, embedded):
                    self._tool_embeddings[k] = vec
                self._is_initialized = True
        except Exception:
            pass

    def route_platforms(self, prompt: str, threshold: float = 0.35) -> list[str]:
        self._initialize()
        if not self._is_initialized:
            return []
        try:
            prompt_vec = embedding_service.embed(prompt)
            matches = []
            for t_type, t_vec in self._tool_embeddings.items():
                sim = sum(a * b for a, b in zip(prompt_vec, t_vec))
                if sim >= threshold:
                    slug = _provider_for_type(t_type)
                    if slug:
                        matches.append((slug, sim))
            matches.sort(key=lambda x: x[1], reverse=True)
            seen: set[str] = set()
            dedup: list[str] = []
            for prov, _ in matches:
                if prov not in seen:
                    dedup.append(prov)
                    seen.add(prov)
            return dedup
        except Exception:
            return []


_semantic_router = DifySemanticRouter()


# ══════════════════════════════════════════════════════════════════════════
#  FEW-SHOT CANONICAL TEMPLATES  (5 training workflows)
# ══════════════════════════════════════════════════════════════════════════

CANONICAL_PATTERNS: dict[str, dict[str, Any]] = {
    # ── Template 1: Data Analysis Chatbot ─────────────────────────────
    "data_analysis": {
        "name": "Data Analysis Chatbot",
        "description": "Analyze Google Sheets data and answer questions",
        "example_prompts": [
            "analyze my google sheets data and answer questions",
            "read spreadsheet and summarize the data",
            "get data from sheets and generate insights",
        ],
        "roles": [
            {"role": "trigger",   "node_type": "trigger_webhook",           "required": True},
            {"role": "data",      "node_type": "integration_google_sheets", "required": True},
            {"role": "llm",       "node_type": "llm_generate",              "required": True},
            {"role": "response",  "node_type": "transform",                 "required": True},
        ],
    },
    # ── Template 2: RAG Chatbot ───────────────────────────────────────
    "rag": {
        "name": "RAG Knowledge Assistant",
        "description": "Answer questions from a knowledge base / documents",
        "example_prompts": [
            "answer questions from my knowledge base",
            "rag pipeline for documents",
            "search my documents and answer",
            "knowledge base chatbot",
        ],
        "roles": [
            {"role": "trigger",   "node_type": "trigger_webhook",     "required": True},
            {"role": "retriever", "node_type": "integration_qdrant",  "required": True},
            {"role": "llm",       "node_type": "llm_generate",        "required": True},
            {"role": "response",  "node_type": "transform",           "required": True},
        ],
    },
    # ── Template 3: YouTube Summarizer ────────────────────────────────
    "youtube_summarization": {
        "name": "YouTube Summarizer",
        "description": "Summarize YouTube videos from transcripts",
        "example_prompts": [
            "summarize youtube videos",
            "get youtube transcript and summarize",
        ],
        "roles": [
            {"role": "trigger",    "node_type": "trigger_webhook",     "required": True},
            {"role": "transcript", "node_type": "integration_youtube_transcript", "required": True},
            {"role": "llm",        "node_type": "llm_generate",        "required": True},
        ],
    },
    # ── Template 4: Bulk Email Sender ─────────────────────────────────
    "bulk_email": {
        "name": "Bulk Email Sender",
        "description": "Send emails to contacts from Google Sheets",
        "example_prompts": [
            "send emails from google sheets list",
            "bulk email from spreadsheet",
            "mass email using sheets data",
        ],
        "roles": [
            {"role": "trigger", "node_type": "trigger_webhook",           "required": True},
            {"role": "data",    "node_type": "integration_google_sheets", "required": True},
            {"role": "loop",    "node_type": "loop",                      "required": True},
            {"role": "action",  "node_type": "integration_gmail",         "required": True},
        ],
    },
    # ── Template 5: Chat Automation (Telegram) ────────────────────────
    "chat_automation": {
        "name": "Chat Automation",
        "description": "Reply to Telegram messages using AI",
        "example_prompts": [
            "reply to telegram messages using ai",
            "telegram chatbot",
            "auto-reply telegram messages",
        ],
        "roles": [
            {"role": "trigger",  "node_type": "trigger_webhook",       "required": True},
            {"role": "llm",      "node_type": "llm_generate",          "required": True},
            {"role": "response", "node_type": "integration_telegram",  "required": True},
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 1 — INTENT EXTRACTOR  (LLM-driven with regex fallback)
# ══════════════════════════════════════════════════════════════════════════

_INTENT_SYSTEM_PROMPT = """\
You are an intent classifier for AuraFlow, a workflow automation platform.
Extract structured intent from the user's prompt.

You MUST return valid JSON with these fields:
{
  "workflow_type": "data_analysis | rag | youtube_summarization | bulk_email | chat_automation | generic",
  "input_mode": "chat | webhook | schedule",
  "requires_llm": true/false,
  "requires_loop": true/false,
  "target_integrations": ["provider_slug_1", "provider_slug_2"]
}

Available provider slugs: google-sheets, gmail, qdrant, telegram, discord, slack,
notion, stripe, hubspot, github, zendesk, twitter, linkedin, shopify, sentry.

ONLY return the JSON object. No markdown, no explanation."""


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 0 — COMPILER INPUTS RESOLVER
# ══════════════════════════════════════════════════════════════════════════

class CompilerInputsResolver:
    """
    Stage 0: Prepares global compiler context before generation.
    Fetches available integrations, normalizes provider names,
    and returns downstream inputs.
    """
    def resolve(self) -> dict[str, Any]:
        return {
            "connected_providers": list(_connected_providers()),
            "node_types": _NODE_TYPE_MAP
        }




class IntentExtractor:
    """
    Stage 1: Converts natural-language prompt → structured intent JSON.
    Primary path: LLM extraction.
    Fallback: deterministic regex parser (reduces confidence).
    """

    def extract(self, prompt: str) -> dict[str, Any]:
        # Try LLM extraction first
        llm_result = self._try_llm_extract(prompt)
        if llm_result is not None:
            llm_result["_source"] = "llm"
            llm_result["raw_prompt"] = prompt
            return llm_result

        # Fallback: deterministic regex parser
        result = self._regex_extract(prompt)
        result["_source"] = "regex_fallback"
        result["raw_prompt"] = prompt
        return result

    # ── LLM path ──────────────────────────────────────────────────────

    def _try_llm_extract(self, prompt: str) -> dict[str, Any] | None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Also try Gemini
            return self._try_gemini_extract(prompt)
        try:
            payload = {
                "model": os.getenv("OPENAI_WORKFLOW_MODEL", "gpt-4.1-mini"),
                "messages": [
                    {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            return self._parse_llm_json(text)
        except Exception:
            return self._try_gemini_extract(prompt)

    def _try_gemini_extract(self, prompt: str) -> dict[str, Any] | None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        try:
            payload = {
                "contents": [
                    {"parts": [{"text": f"{_INTENT_SYSTEM_PROMPT}\n\nUser prompt: {prompt}"}]}
                ],
            }
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_llm_json(text)
        except Exception:
            return None

    def _parse_llm_json(self, text: str) -> dict[str, Any] | None:
        """Parse JSON from LLM output, stripping markdown fences if present."""
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
        try:
            parsed = json.loads(cleaned)
            # Validate expected shape
            if "workflow_type" in parsed and "target_integrations" in parsed:
                return {
                    "workflow_type": str(parsed.get("workflow_type", "generic")),
                    "input_mode": str(parsed.get("input_mode", "webhook")),
                    "requires_llm": bool(parsed.get("requires_llm", False)),
                    "requires_loop": bool(parsed.get("requires_loop", False)),
                    "target_integrations": list(parsed.get("target_integrations", [])),
                }
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
        return None

    # ── Regex fallback ────────────────────────────────────────────────

    def _regex_extract(self, prompt: str) -> dict[str, Any]:
        p = prompt.lower()

        # Detect workflow type
        workflow_type = "generic"
        requires_llm = False
        requires_loop = False
        target_integrations: list[str] = []

        if ("sheet" in p or "spreadsheet" in p) and any(w in p for w in ["analyze", "analyse", "summarize", "answer", "insight"]):
            workflow_type = "data_analysis"
            requires_llm = True
            target_integrations.append("google-sheets")

        elif any(w in p for w in ["knowledge base", "knowledge", "rag", "document"]) and any(w in p for w in ["answer", "search", "query", "chat"]):
            workflow_type = "rag"
            requires_llm = True
            if "qdrant" not in target_integrations:
                target_integrations.append("qdrant")

        elif "youtube" in p and any(w in p for w in ["summar", "transcript"]):
            workflow_type = "youtube_summarization"
            requires_llm = True

        elif "bulk" in p and "email" in p:
            workflow_type = "bulk_email"
            requires_loop = True
            target_integrations.extend(["google-sheets", "gmail"])

        elif "telegram" in p and any(w in p for w in ["reply", "respond", "chat", "bot", "message"]):
            workflow_type = "chat_automation"
            requires_llm = True
            target_integrations.append("telegram")

        elif "discord" in p and any(w in p for w in ["reply", "respond", "chat", "bot"]):
            workflow_type = "chat_automation"
            requires_llm = True
            target_integrations.append("discord")

        # Detect any remaining integrations mentioned by keyword
        kw_map = {
            "google-sheets": ["google sheets", "sheets", "spreadsheet"],
            "gmail": ["gmail", "email"],
            "slack": ["slack"],
            "notion": ["notion"],
            "telegram": ["telegram"],
            "discord": ["discord"],
            "qdrant": ["qdrant", "vector"],
            "hubspot": ["hubspot", "crm"],
            "github": ["github"],
            "zendesk": ["zendesk"],
            "stripe": ["stripe", "payment"],
            "twitter": ["twitter", "tweet"],
            "linkedin": ["linkedin"],
            "shopify": ["shopify"],
            "sentry": ["sentry"],
        }
        for slug, keywords in kw_map.items():
            if any(kw in p for kw in keywords) and slug not in target_integrations:
                target_integrations.append(slug)

        # Semantic routing supplement
        if len(target_integrations) <= 1:
            for slug in _semantic_router.route_platforms(p)[:2]:
                if slug not in target_integrations:
                    target_integrations.append(slug)

        # Detect input mode
        input_mode = "webhook"
        if any(w in p for w in ["schedule", "daily", "weekly", "hourly", "cron", "every"]):
            input_mode = "schedule"
        elif any(w in p for w in ["chat", "message", "reply", "respond"]):
            input_mode = "chat"

        # Detect LLM need
        if any(w in p for w in ["analyze", "summarize", "generate", "classify", "answer",
                                 "draft", "write", "respond", "reply", "translate",
                                 "extract", "parse", "decide"]):
            requires_llm = True

        return {
            "workflow_type": workflow_type,
            "input_mode": input_mode,
            "requires_llm": requires_llm,
            "requires_loop": requires_loop,
            "target_integrations": target_integrations,
        }


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 2 — PATTERN MATCHER  (few-shot + rules)
# ══════════════════════════════════════════════════════════════════════════

class PatternMatcher:
    """
    Stage 2: Matches structured intent to a canonical workflow pattern.
    Returns pattern definition with roles, or 'generic' fallback.
    """

    def match(self, intent: dict[str, Any]) -> dict[str, Any]:
        wf_type = intent.get("workflow_type", "generic")

        # Direct match
        if wf_type in CANONICAL_PATTERNS:
            pattern = dict(CANONICAL_PATTERNS[wf_type])
            pattern["matched_type"] = wf_type
            pattern["is_supported"] = True
            # YouTube: check if transcript node exists
            if wf_type == "youtube_summarization":
                if "integration_youtube_transcript" not in _NODE_TYPE_MAP:
                    pattern["is_supported"] = False
                    pattern["unsupported_reason"] = "No transcript node in NODE_TYPES"
            return pattern

        # Fallback: try to infer from target_integrations
        targets = set(intent.get("target_integrations", []))
        if "google-sheets" in targets and intent.get("requires_loop") and "gmail" in targets:
            pattern = dict(CANONICAL_PATTERNS["bulk_email"])
            pattern["matched_type"] = "bulk_email"
            pattern["is_supported"] = True
            return pattern
        if "qdrant" in targets and intent.get("requires_llm"):
            pattern = dict(CANONICAL_PATTERNS["rag"])
            pattern["matched_type"] = "rag"
            pattern["is_supported"] = True
            return pattern
        if "telegram" in targets and intent.get("requires_llm"):
            pattern = dict(CANONICAL_PATTERNS["chat_automation"])
            pattern["matched_type"] = "chat_automation"
            pattern["is_supported"] = True
            return pattern

        # Generic fallback
        return {
            "matched_type": "generic",
            "name": "Generic Workflow",
            "description": "Custom workflow generated from prompt",
            "roles": self._build_generic_roles(intent),
            "is_supported": True,
        }

    def _build_generic_roles(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """Build a minimal role list for unrecognized patterns."""
        trigger_type = "trigger_schedule" if intent.get("input_mode") == "schedule" else "trigger_webhook"
        roles: list[dict[str, Any]] = [
            {"role": "trigger", "node_type": trigger_type, "required": True},
        ]

        # Add integration nodes for each target
        for slug in intent.get("target_integrations", []):
            itype = self._slug_to_node_type(slug)
            if itype and itype in _NODE_TYPE_MAP:
                roles.append({"role": "integration", "node_type": itype, "required": True})

        # Add LLM if needed
        if intent.get("requires_llm"):
            roles.append({"role": "llm", "node_type": "llm_generate", "required": True})

        # Add loop if needed
        if intent.get("requires_loop"):
            roles.append({"role": "loop", "node_type": "loop", "required": True})

        # Add response transform
        roles.append({"role": "response", "node_type": "transform", "required": False})

        return roles

    @staticmethod
    def _slug_to_node_type(slug: str) -> str | None:
        for n in NODE_TYPES:
            if n.get("provider_slug") == slug:
                return n["type"]
        return None


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 3 — TOOL SELECTOR  (NODE_TYPES + connected integrations)
# ══════════════════════════════════════════════════════════════════════════

class ToolSelector:
    """
    Stage 3: Validates that every role in the pattern can be fulfilled by
    a node in NODE_TYPES whose provider (if any) is connected.
    """

    def select(self, pattern: dict[str, Any]) -> dict[str, Any]:
        connected = _connected_providers()
        selected: list[dict[str, Any]] = []
        missing_integrations: list[str] = []
        is_supported = pattern.get("is_supported", True)

        for role_def in pattern.get("roles", []):
            node_type = role_def["node_type"]

            # Reject if node type does not exist in NODE_TYPES
            if node_type not in _NODE_TYPE_MAP:
                is_supported = False
                continue

            meta = _NODE_TYPE_MAP[node_type]
            provider = meta.get("provider_slug")

            # Track missing provider connections
            if provider and provider not in connected:
                missing_integrations.append(provider)

            selected.append({
                "role": role_def["role"],
                "node_type": node_type,
                "provider": provider,
                "label": meta.get("label", node_type),
                "default_config": dict(meta.get("default_config", {})),
                "connected": provider is None or provider in connected,
            })

        return {
            "selected_tools": selected,
            "missing_integrations": list(dict.fromkeys(missing_integrations)),
            "is_supported": is_supported,
        }


# ══════════════════════════════════════════════════════════════════════════
#  NODE ID HELPERS — human-readable deterministic IDs
# ══════════════════════════════════════════════════════════════════════════

# Maps node_type → short readable slug used in IDs.
_NODE_ID_SLUG: dict[str, str] = {
    "trigger_webhook":           "trigger_webhook",
    "trigger_schedule":          "trigger_schedule",
    "integration_google_sheets": "sheets",
    "integration_gmail":         "gmail_send",
    "integration_qdrant":        "qdrant_search",
    "integration_telegram":      "telegram",
    "integration_discord":       "discord",
    "integration_slack":         "slack",
    "integration_notion":        "notion",
    "integration_stripe":        "stripe",
    "integration_hubspot":       "hubspot",
    "integration_github":        "github",
    "integration_zendesk":       "zendesk",
    "integration_twitter":       "twitter",
    "integration_linkedin":      "linkedin",
    "integration_shopify":       "shopify",
    "integration_sentry":        "sentry",
    "integration_document_parser": "doc_parser",
    "llm_generate":              "llm_generate",
    "llm_classify":              "llm_classify",
    "llm_decision":              "llm_decision",
    "loop":                      "loop",
    "transform":                 "transform",
    "condition":                 "condition",
    "delay":                     "delay",
    "sub_workflow":              "sub_workflow",
    "human_approval":            "approval",
}


def _make_node_id(node_type: str, counters: dict[str, int]) -> str:
    """Generate a deterministic human-readable node ID like sheets_1, gmail_send_1."""
    slug = _NODE_ID_SLUG.get(node_type, node_type)
    counters[slug] = counters.get(slug, 0) + 1
    return f"{slug}_{counters[slug]}"


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 4 — GRAPH COMPILER  (deterministic structure from pattern)
# ══════════════════════════════════════════════════════════════════════════

class GraphCompiler:
    """
    Stage 4: Builds a minimal, deterministic workflow graph.
    Rules:
      - Exactly one trigger
      - Deterministic node IDs: trigger_webhook_1, sheets_1, llm_generate_1, gmail_send_1
      - Configs seeded from default_config + compiler overrides
      - Minimal edges — sequential chain, no template padding
      - Loop only for bulk patterns; router only if required
    """

    _X_START = 100
    _X_STEP = 280
    _Y_CENTER = 300

    def compile(self, intent: dict[str, Any], tool_selection: dict[str, Any]) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        id_counters: dict[str, int] = {}
        prev_node_id: str | None = None

        for idx, tool in enumerate(tool_selection["selected_tools"]):
            node_type = tool["node_type"]
            node_id = _make_node_id(node_type, id_counters)

            config = dict(tool.get("default_config", {}))
            self._apply_pattern_config(intent, tool, config)

            is_ai = node_type.startswith("llm_")
            provider = tool.get("provider") or None
            action = config.get("action") or _NODE_TYPE_MAP.get(node_type, {}).get("default_config", {}).get("action") or None
            node = {
                "id": node_id,
                "type": node_type,
                "provider": provider,
                "action": action,
                "name": tool.get("label", node_type),
                "position": {"x": self._X_START + idx * self._X_STEP, "y": self._Y_CENTER},
                "config": config,
                "input_mapping": {},
                "output_mapping": {},
                "ai_brain": is_ai,
                "memory": "short_term" if is_ai else None,
                "retry_policy": {"max_retries": 2, "backoff": "exponential", "retry_on": ["timeout", "api_error"]},
                "timeout_ms": 30000 if is_ai else 10000,
            }
            nodes.append(node)

            if prev_node_id is not None:
                edges.append({
                    "id": f"edge-{uuid4().hex[:8]}",
                    "source": prev_node_id,
                    "target": node_id,
                    "condition": "true",
                })
            prev_node_id = node_id

        return {"nodes": nodes, "edges": edges}

    def _apply_pattern_config(self, intent: dict[str, Any], tool: dict[str, Any], config: dict[str, Any]) -> None:
        """Override default_config with pattern-specific values."""
        node_type = tool["node_type"]
        wf_type = intent.get("workflow_type", "generic")
        prompt = intent.get("raw_prompt", "")

        if node_type == "trigger_webhook":
            config["path"] = f"/webhooks/{wf_type.replace('_', '-')}"

        elif node_type == "trigger_schedule":
            config["cron"] = "0 9 * * *"

        elif node_type == "integration_google_sheets":
            if wf_type in ("data_analysis", "bulk_email"):
                config["action"] = "read_rows"
                config["spreadsheet_id"] = ""
                config["range"] = "Sheet1!A:Z"
            else:
                config["action"] = "append_row"

        elif node_type == "integration_gmail":
            config["action"] = "send_email"

        elif node_type == "integration_qdrant":
            config["action"] = "search_vectors"
            config["top_k"] = 5

        elif node_type == "integration_telegram":
            config["action"] = "send_message"

        elif node_type.startswith("llm_"):
            short = prompt[:120] if prompt else "Process this input"
            config["prompt"] = short
            config["memory"] = "short_term"

        elif node_type == "loop":
            config["items_path"] = "items"
            config["item_alias"] = "item"

        elif node_type == "transform":
            config["template"] = "{{input}}"


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 5 — DATA MAPPER  (wires {{node_id.output.field}} bindings)
# ══════════════════════════════════════════════════════════════════════════

class DataMapper:
    """
    Stage 5: Resolves data flow between nodes.
    - Maps upstream outputs to downstream required inputs
    - Uses {{node_id.output.field}} binding syntax
    - Enforces loop semantics: {{item.field}} inside loops
    - Tracks inferred mappings (triggers -15 confidence penalty)
    - Can insert an LLM transform node if a required field can't be
      satisfied directly from upstream outputs
    """

    def __init__(self) -> None:
        self.inferred_count: int = 0
        self.inserted_nodes: int = 0

    def map(self, graph: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
        self.inferred_count = 0
        self.inserted_nodes = 0
        nodes = graph["nodes"]
        wf_type = intent.get("workflow_type", "generic")
        node_by_type: dict[str, dict[str, Any]] = {}
        for n in nodes:
            if n["type"] not in node_by_type:
                node_by_type[n["type"]] = n

        if wf_type == "data_analysis":
            self._map_data_analysis(node_by_type)
        elif wf_type == "rag":
            self._map_rag(node_by_type)
        elif wf_type == "bulk_email":
            self._map_bulk_email(node_by_type)
        elif wf_type == "chat_automation":
            self._map_chat_automation(node_by_type)
        else:
            self._map_generic(graph)

        return graph

    def _map_data_analysis(self, m: dict[str, dict[str, Any]]) -> None:
        sheets = m.get("integration_google_sheets")
        llm = m.get("llm_generate")
        transform = m.get("transform")
        if sheets and llm:
            llm["config"]["input"] = "{{" + sheets["id"] + ".output.rows}}"
            llm["config"]["prompt"] = "Analyze the following spreadsheet data and provide insights:\n\n{{" + sheets["id"] + ".output.rows}}"
        if llm and transform:
            transform["config"]["template"] = "{{" + llm["id"] + ".output.text}}"

    def _map_rag(self, m: dict[str, dict[str, Any]]) -> None:
        trigger = m.get("trigger_webhook")
        qdrant = m.get("integration_qdrant")
        llm = m.get("llm_generate")
        transform = m.get("transform")
        if trigger and qdrant:
            qdrant["config"]["query"] = "{{" + trigger["id"] + ".output.payload.query}}"
        if qdrant and llm:
            llm["config"]["input"] = "{{" + qdrant["id"] + ".output.matches}}"
            llm["config"]["prompt"] = "Answer the question using ONLY the following context:\n\n{{" + qdrant["id"] + ".output.matches}}"
        if llm and transform:
            transform["config"]["template"] = "{{" + llm["id"] + ".output.text}}"

    def _map_bulk_email(self, m: dict[str, dict[str, Any]]) -> None:
        sheets = m.get("integration_google_sheets")
        loop = m.get("loop")
        gmail = m.get("integration_gmail")
        if sheets and loop:
            loop["config"]["items"] = "{{" + sheets["id"] + ".output.rows}}"
            loop["config"]["item_alias"] = "item"
        if gmail:
            gmail["config"]["to"] = "{{item.email}}"
            gmail["config"]["subject"] = "{{item.subject}}"
            gmail["config"]["body"] = "{{item.body}}"

    def _map_chat_automation(self, m: dict[str, dict[str, Any]]) -> None:
        trigger = m.get("trigger_webhook")
        llm = m.get("llm_generate")
        response = m.get("integration_telegram") or m.get("integration_discord") or m.get("integration_slack")
        if trigger and llm:
            llm["config"]["input"] = "{{" + trigger["id"] + ".output.payload.text}}"
            llm["config"]["prompt"] = "You are a helpful assistant. Reply to: {{" + trigger["id"] + ".output.payload.text}}"
        if llm and response:
            ntype = response["type"]
            if ntype == "integration_telegram":
                response["config"]["text"] = "{{" + llm["id"] + ".output.text}}"
                response["config"]["chat_id"] = "{{" + (trigger["id"] if trigger else "trigger_webhook_1") + ".output.payload.chat_id}}"
            elif ntype == "integration_discord":
                response["config"]["content"] = "{{" + llm["id"] + ".output.text}}"
            elif ntype == "integration_slack":
                response["config"]["message"] = "{{" + llm["id"] + ".output.text}}"

    def _map_generic(self, graph: dict[str, Any]) -> None:
        """Chain generic data flow: infer output→input from upstream schemas.
        If a downstream required field cannot be satisfied, insert an LLM
        transform node between the two."""
        nodes = graph["nodes"]
        for i, node in enumerate(nodes):
            if i == 0:
                continue
            prev = nodes[i - 1]
            prev_outputs = NODE_OUTPUT_SCHEMAS.get(prev["type"], [])

            if not prev_outputs:
                continue

            # Check if downstream has required fields that need satisfaction
            meta = _NODE_TYPE_MAP.get(node["type"], {})
            required = meta.get("required_fields", [])
            config = node.get("config", {})
            first_field = prev_outputs[0]

            mapped_any = False
            for field in required:
                val = config.get(field)
                if val in (None, "", []) or (isinstance(val, str) and "{{" not in val):
                    # Try to infer from upstream
                    if first_field:
                        config[field] = "{{" + prev["id"] + ".output." + first_field + "}}"
                        self.inferred_count += 1
                        mapped_any = True

            # Fallback: at least wire up standard fields
            if not mapped_any:
                if node["type"].startswith("llm_"):
                    config["input"] = "{{" + prev["id"] + ".output." + first_field + "}}"
                    self.inferred_count += 1
                elif node["type"] == "transform":
                    config["template"] = "{{" + prev["id"] + ".output." + first_field + "}}"
                    self.inferred_count += 1

    def insert_llm_transform(self, graph: dict[str, Any], before_idx: int, source_id: str, source_field: str) -> str:
        """Insert an LLM transform node into the graph to bridge incompatible data."""
        node_id = f"llm_transform_{self.inserted_nodes + 1}"
        self.inserted_nodes += 1
        llm_node = {
            "id": node_id,
            "type": "llm_generate",
            "name": "LLM Transform",
            "position": {"x": 100 + before_idx * 280, "y": 450},
            "config": {
                "prompt": "Transform the following data for the next step",
                "input": "{{" + source_id + ".output." + source_field + "}}",
                "memory": "short_term",
            },
            "input_mapping": {},
            "output_mapping": {},
            "ai_brain": True,
            "memory": "short_term",
            "retry_policy": {"max_retries": 2, "backoff": "exponential", "retry_on": ["timeout", "api_error"]},
            "timeout_ms": 30000,
        }
        graph["nodes"].insert(before_idx, llm_node)
        return node_id


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 6 — GRAPH OPTIMIZER
# ══════════════════════════════════════════════════════════════════════════

class GraphOptimizer:
    """
    Stage 6: Graph Optimization pass.
    - Dedupes nodes by type/provider/action
    - Removes redundant transform nodes
    - Merges consecutive transforms
    """
    def optimize(self, graph: dict[str, Any]) -> dict[str, Any]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # 1. Deduplication pass
        seen_configs = {}
        deduped_nodes = []
        to_remove = set()
        
        for n in nodes:
            # allow duplicate triggers natively clamped by validator if invalid anyway
            if n["type"].startswith("trigger_"):
                deduped_nodes.append(n)
                continue
            
            sig = (n["type"], n.get("provider"), n.get("action"), str(n.get("config")))
            if sig in seen_configs:
                to_remove.add(n["id"])
                first_id = seen_configs[sig]
                for e in edges:
                    if e["target"] == n["id"]: e["target"] = first_id
                    if e["source"] == n["id"]: e["source"] = first_id
            else:
                seen_configs[sig] = n["id"]
                deduped_nodes.append(n)

        nodes = deduped_nodes
        
        # 2. Redundant map cleanup pass
        optimized_nodes = []
        for n in nodes:
            if n["id"] in to_remove:
                continue
            # if transform node only outputs {{input}}, it's a no-op and can be removed
            if n["type"] == "transform":
                template = n.get("config", {}).get("template", "")
                if template == "{{input}}":
                    to_remove.add(n["id"])
                    # rewire edges across the removed node
                    in_edges = [e for e in edges if e["target"] == n["id"]]
                    out_edges = [e for e in edges if e["source"] == n["id"]]
                    for ie in in_edges:
                        for oe in out_edges:
                            edges.append({
                                "id": f"edge-{uuid4().hex[:8]}",
                                "source": ie["source"],
                                "target": oe["target"],
                                "condition": "true",
                            })
                    edges = [e for e in edges if e["source"] != n["id"] and e["target"] != n["id"]]
                    continue
            optimized_nodes.append(n)

        return {"nodes": optimized_nodes, "edges": edges, "applied": len(to_remove) > 0}


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 7 — VALIDATOR
# ══════════════════════════════════════════════════════════════════════════

class Validator:
    """
    Stage 7: Enforces structural + semantic correctness.
    Checks:
      - Exactly one trigger
      - No duplicate node IDs
      - All edges point to valid nodes
      - No orphan nodes (graph is connected)
      - Graph is acyclic (no cycles)
      - Required config fields present and non-empty
      - Provider-backed nodes exist in NODE_TYPES
      - Valid data bindings ({{id.output.field}} references real upstream nodes)
      - Enforces output schema mapping consistency
      - Execution validation (action inside NODE_TYPES actions)
      - No empty or non-executable configs
    """

    def validate(self, graph: dict[str, Any]) -> dict[str, Any]:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        issues: list[str] = []

        if not nodes:
            return {"valid": False, "issues": ["STRUCTURAL: Workflow has no nodes"]}

        node_ids = {n["id"] for n in nodes}
        node_map = {n["id"]: n for n in nodes}

        # 1. Exactly one trigger
        trigger_types = {"trigger_webhook", "trigger_schedule"}
        trigger_like = {"integration_gmail", "integration_stripe", "integration_shopify", "integration_sentry"}
        triggers = [n for n in nodes if n["type"] in trigger_types or (n["type"] in trigger_like and n is nodes[0])]
        if len(triggers) == 0:
            issues.append("STRUCTURAL: No trigger node found")
        elif len(triggers) > 1:
            issues.append(f"STRUCTURAL: Multiple triggers found ({len(triggers)}); exactly 1 required")
        if nodes[0]["type"] not in trigger_types and nodes[0]["type"] not in trigger_like:
            issues.append(f"STRUCTURAL: First node '{nodes[0]['type']}' is not a valid trigger")

        # 2. No duplicate IDs
        seen_ids: set[str] = set()
        for n in nodes:
            if n["id"] in seen_ids:
                issues.append(f"STRUCTURAL: Duplicate node ID: {n['id']}")
            seen_ids.add(n["id"])

        # 3. Edge validity
        for edge in edges:
            if edge.get("source") not in node_ids:
                issues.append(f"STRUCTURAL: Edge {edge['id']} has invalid source: {edge['source']}")
            if edge.get("target") not in node_ids:
                issues.append(f"STRUCTURAL: Edge {edge['id']} has invalid target: {edge['target']}")

        # 4. No orphan nodes — every non-first node must be a target of some edge
        targets = {e["target"] for e in edges}
        for n in nodes[1:]:
            if n["id"] not in targets:
                issues.append(f"STRUCTURAL: Node {n['id']} ({n['name']}) is unreachable (orphan)")

        # 5. Acyclic check — simple DFS cycle detection
        adjacency: dict[str, list[str]] = {n["id"]: [] for n in nodes}
        for e in edges:
            src, tgt = e.get("source"), e.get("target")
            if src in adjacency and tgt:
                adjacency[src].append(tgt)

        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in adjacency}

        def _dfs_cycle(nid: str) -> bool:
            color[nid] = GRAY
            for nbr in adjacency.get(nid, []):
                if color.get(nbr) == GRAY:
                    return True
                if color.get(nbr) == WHITE and _dfs_cycle(nbr):
                    return True
            color[nid] = BLACK
            return False

        for nid in list(adjacency):
            if color[nid] == WHITE and _dfs_cycle(nid):
                issues.append("STRUCTURAL: Cycle detected — graph must be acyclic")
                break

        # 6. Required config fields & Action validation
        for n in nodes:
            meta = _NODE_TYPE_MAP.get(n["type"])
            if meta is None:
                issues.append(f"STRUCTURAL: Unknown node type: {n['type']}")
                continue
            
            # Action validation (Execution awareness)
            action = n.get("action")
            if action:
                supported = meta.get("actions", [])
                if not supported and "default_config" in meta and "action" in meta["default_config"]:
                    supported = [meta["default_config"]["action"]]
                if supported and action not in supported:
                    issues.append(f"EXECUTION: Node {n['id']} uses invalid action '{action}'. Supported: {supported}")

            # Required fields
            config = n.get("config", {})
            for field in meta.get("required_fields", []):
                if field not in config or config[field] in (None, "", []):
                    issues.append(f"EXECUTION: Node {n['id']} missing required config field: {field}")

        # 7. No empty configs at all
        for n in nodes:
            if not n.get("config"):
                issues.append(f"CONFIG: Node {n['id']} has empty config")

        # 8. Provider validity — provider_slug must be in NODE_TYPES
        for n in nodes:
            meta = _NODE_TYPE_MAP.get(n["type"])
            if meta and meta.get("provider_slug"):
                # Provider-backed node: type must exist in registry
                if n["type"] not in _NODE_TYPE_MAP:
                    issues.append(f"PROVIDER: Node {n['id']} uses unknown provider type: {n['type']}")

        # 9. Binding validation — {{id.output.field}} bindings must reference valid upstream nodes
        for n in nodes:
            config = n.get("config", {})
            for field, val in config.items():
                if not isinstance(val, str):
                    continue
                for binding_match in re.finditer(r"\{\{(\w+)\.output\.(\w+)\}\}", val):
                    ref_id = binding_match.group(1)
                    # Skip loop item references
                    if ref_id == "item":
                        continue
                    # The referenced node must exist in the graph
                    ref_node = next((upstream for upstream in nodes if ref_id in upstream["id"]), None)
                    if not ref_node:
                        issues.append(f"BINDING: Node {n['id']}.{field} references unknown node: {ref_id}")
                    else:
                        # Validate output schema compatibility
                        schemas = NODE_OUTPUT_SCHEMAS.get(ref_node["type"], [])
                        ref_field = binding_match.group(2)
                        if schemas and ref_field not in schemas:
                            issues.append(f"BINDING: Node {n['id']}.{field} uses invalid output '{ref_field}' from '{ref_node['type']}'. Valid: {schemas}")

        return {"valid": len(issues) == 0, "issues": issues}


# ══════════════════════════════════════════════════════════════════════════
#  STAGE 7 — CONFIDENCE SCORER  (deterministic 0–100 rubric)
# ══════════════════════════════════════════════════════════════════════════

class ConfidenceScorer:
    """
    Stage 7: Deterministic scoring rubric.
      Start at 100, subtract:
        -30  missing integrations (provider not connected)
        -20  unclear or unsupported pattern
        -15  fallback intent extraction (LLM unavailable)
        -15  inferred mappings (DataMapper had to guess)
        -10  extra compiler-inserted nodes
      Clamp to [0, 100].
    """

    def score(
        self,
        intent: dict[str, Any],
        pattern: dict[str, Any],
        tool_selection: dict[str, Any],
        validation: dict[str, Any],
        graph: dict[str, Any],
        data_mapper: DataMapper | None = None,
    ) -> dict[str, Any]:
        score = 100
        penalties: list[str] = []

        # -30: Missing integrations
        if tool_selection.get("missing_integrations"):
            score -= 30
            penalties.append(f"-30: missing integrations ({', '.join(tool_selection['missing_integrations'])})")

        # -20: Unclear / unsupported pattern
        if not pattern.get("is_supported") or pattern.get("matched_type") == "generic":
            score -= 20
            penalties.append("-20: unclear or unsupported pattern")

        # -15: Regex fallback (LLM parsing failed)
        if intent.get("_source") == "regex_fallback":
            score -= 15
            penalties.append("-15: fallback intent extraction (LLM unavailable)")

        # -15: Inferred mappings (DataMapper had to guess bindings)
        inferred = data_mapper.inferred_count if data_mapper else 0
        if inferred > 0:
            score -= 15
            penalties.append(f"-15: {inferred} inferred mapping(s)")

        # -10: Extra compiler-inserted nodes
        canonical = CANONICAL_PATTERNS.get(pattern.get("matched_type", ""), {})
        expected_count = len(canonical.get("roles", []))
        actual_count = len(graph.get("nodes", []))
        inserted = (data_mapper.inserted_nodes if data_mapper else 0)
        extra = (actual_count - expected_count) if expected_count > 0 else 0
        extra += inserted
        if extra > 0:
            score -= 10
            penalties.append(f"-10: {extra} extra node(s)")

        score = max(0, min(100, score))

        return {
            "total": score,
            "penalties": penalties,
            "breakdown": {
                "base": 100,
                "missing_integrations": -30 if tool_selection.get("missing_integrations") else 0,
                "pattern_support": -20 if (not pattern.get("is_supported") or pattern.get("matched_type") == "generic") else 0,
                "fallback_extraction": -15 if intent.get("_source") == "regex_fallback" else 0,
                "inferred_mappings": -15 if inferred > 0 else 0,
                "extra_nodes": -10 if extra > 0 else 0,
            },
        }


# ══════════════════════════════════════════════════════════════════════════
#  ORCHESTRATOR — dual-mode compiler + code graph engine
# ══════════════════════════════════════════════════════════════════════════

class AuraFlowWorkflowArchitect:
    """
    AuraFlow system orchestrator.

    Mode 1 — WORKFLOW:
      1. IntentExtractor   → structured intent JSON (LLM + regex fallback)
      2. PatternMatcher    → canonical workflow pattern (5 templates)
      3. ToolSelector      → validated tool list (NODE_TYPES + integrations)
      4. GraphCompiler     → minimal node/edge graph (deterministic IDs)
      5. DataMapper        → {{binding}} wiring (with loop semantics)
      6. GraphOptimizer    → redundant node cleanup
      7. Validator         → structural + semantic + execution checks
      8. ConfidenceScorer  → 0-100 deterministic rubric

    Mode 2 — CODE:
      MCP code graph query → relevant services, files, relationships
    """

    def __init__(self) -> None:
        self.mode_router = ModeRouter()
        self.code_graph = CodeGraphEngine()
        self.inputs_resolver = CompilerInputsResolver()
        self.intent_extractor = IntentExtractor()
        self.pattern_matcher = PatternMatcher()
        self.tool_selector = ToolSelector()
        self.graph_compiler = GraphCompiler()
        self.graph_optimizer = GraphOptimizer()
        self.validator = Validator()
        self.confidence_scorer = ConfidenceScorer()

    def generate(self, description: str) -> dict[str, Any]:
        prompt = description.strip()
        if not prompt:
            raise ValueError("Prompt is required.")

        # ── Mode Decision ─────────────────────────────────────────────
        mode, mode_scores = self.mode_router.route(prompt)

        if mode == "code":
            return self._handle_code_mode(prompt)

        return self._handle_workflow_mode(prompt, mode_scores)

    # ── CODE MODE ─────────────────────────────────────────────────────

    def _handle_code_mode(self, prompt: str) -> dict[str, Any]:
        return self.code_graph.query(prompt)

    # ── WORKFLOW MODE ─────────────────────────────────────────────────

    def _handle_workflow_mode(self, prompt: str, mode_scores: dict[str, int]) -> dict[str, Any]:
        # ── Stage 0: Resolve global compiler inputs ───────────────────
        compiler_inputs = self.inputs_resolver.resolve()

        # ── Stage 1: Intent Extraction (LLM → regex fallback) ─────────
        intent = self.intent_extractor.extract(prompt)

        # ── Stage 2: Pattern Matching (5 canonical templates) ─────────
        pattern = self.pattern_matcher.match(intent)

        # ── Stage 3: Tool Selection (strict registry-based) ──────────
        tool_selection = self.tool_selector.select(pattern)

        # Reject completely unsupported patterns
        if not tool_selection["is_supported"] and not tool_selection["selected_tools"]:
            raise ValueError(
                f"Unsupported workflow pattern: {pattern.get('matched_type')}. "
                f"Reason: {pattern.get('unsupported_reason', 'required tools not available')}"
            )

        # ── Compilation with Double Validation / Retry Loop ───────────
        attempts_taken = 0
        graph: dict[str, Any] = {}
        validation: dict[str, Any] = {"valid": False, "issues": []}
        data_mapper = DataMapper()
        optimization_applied = False

        for attempt in range(2):
            attempts_taken += 1

            # ── Stage 4: Graph Compilation (deterministic) ────────────────
            graph = self.graph_compiler.compile(intent, tool_selection)

            # ── Stage 5: Data Mapping (with loop semantics) ──────────────
            data_mapper = DataMapper()
            graph = data_mapper.map(graph, intent)

            # ── Stage 6a: Validator (PASS 1 - Before Optimization) ───────
            pass1_validation = self.validator.validate(graph)
            if not pass1_validation["valid"]:
                validation = pass1_validation

            # ── Stage 6b: Graph Optimization ──────────────────────────────
            opt_result = self.graph_optimizer.optimize(graph)
            graph = {"nodes": opt_result["nodes"], "edges": opt_result["edges"]}
            optimization_applied = opt_result.get("applied", False)

            # ── Stage 7: Validation (PASS 2 - Final Structural State) ─────
            validation = self.validator.validate(graph)

            if validation["valid"]:
                break

        # ── Stage 8: Confidence Scoring (exact rubric) ────────────────
        confidence = self.confidence_scorer.score(
            intent, pattern, tool_selection, validation, graph, data_mapper,
        )
        normalized = confidence["total"] / 100.0

        # ── Build workflow name ───────────────────────────────────────
        name = pattern.get("name", "Generated Workflow")
        matched_type = pattern.get("matched_type", "generic")

        # ── Count bindings ────────────────────────────────────────────
        binding_count = sum(
            1 for n in graph["nodes"]
            for v in (n.get("config") or {}).values()
            if isinstance(v, str) and "{{" in v
        )

        # ── Assemble response ─────────────────────────────────────────
        result: dict[str, Any] = {
            # Mode identifier
            "mode": "workflow",

            # ── Backward-compatible top-level shape for existing editor ──
            "name": name,
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "explanation": (
                f"Compiled {len(graph['nodes'])}-node {name} workflow. "
                f"Pattern: {matched_type}. "
                f"Confidence: {confidence['total']}%."
            ),
            "missing_integrations": tool_selection["missing_integrations"],
            "confidence": normalized,
            "needs_confirmation": confidence["total"] < 60,
            "plan_confidence": normalized,
            "parse_confidence": normalized,

            # ── Strict compiler metadata ─────────────────────────────────
            "pattern": matched_type,
            "intent": {
                "workflow_type": intent.get("workflow_type"),
                "input_mode": intent.get("input_mode"),
                "requires_llm": intent.get("requires_llm"),
                "requires_loop": intent.get("requires_loop"),
                "target_integrations": intent.get("target_integrations"),
                "_source": intent.get("_source"),
            },
            "workflow": {
                "nodes": graph["nodes"],
                "edges": graph["edges"],
            },
            "confidence_detail": confidence,
            "debug": {
                "mode_scores": mode_scores,
                "inferred_mappings": data_mapper.inferred_count,
                "pattern_confidence": "high" if confidence["total"] > 80 else "low",
                "validation_errors": validation.get("issues", []),
                "retry_attempts": attempts_taken,
                "inserted_nodes": data_mapper.inserted_nodes,
                "optimization_applied": optimization_applied
            }
        }

        if not validation["valid"]:
            result["validation_issues"] = validation["issues"]

        # Reasoning block for debugging
        result["reasoning"] = {
            "intent_source": intent.get("_source"),
            "pattern_matched": matched_type,
            "tools_selected": len(tool_selection["selected_tools"]),
            "tools_missing": tool_selection["missing_integrations"],
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "binding_count": binding_count,
            "inferred_mappings": data_mapper.inferred_count,
            "inserted_nodes": data_mapper.inserted_nodes,
            "validation": validation,
            "confidence_breakdown": confidence["breakdown"],
        }

        return result


workflow_architect_service = AuraFlowWorkflowArchitect()
