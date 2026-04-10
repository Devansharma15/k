from __future__ import annotations

import re
from typing import Any


NODE_META: dict[str, dict[str, str]] = {
    "trigger_webhook": {"stage": "trigger", "label": "Webhook Trigger"},
    "trigger_schedule": {"stage": "trigger", "label": "Scheduled Trigger"},
    "integration_stripe": {"stage": "trigger", "label": "Stripe Trigger"},
    "integration_gmail": {"stage": "trigger", "label": "Gmail Trigger"},
    "integration_http": {"stage": "enrich", "label": "HTTP Enrichment"},
    "integration_database": {"stage": "enrich", "label": "Knowledge Lookup"},
    "integration_google_sheets": {"stage": "action", "label": "Google Sheets Action"},
    "llm_generate": {"stage": "process", "label": "LLM Generate"},
    "llm_classify": {"stage": "process", "label": "LLM Classify"},
    "llm_decision": {"stage": "process", "label": "LLM Decision"},
    "transform": {"stage": "process", "label": "Transform"},
    "condition": {"stage": "branch", "label": "Condition Branch"},
    "loop": {"stage": "branch", "label": "Loop Iterator"},
    "human_approval": {"stage": "branch", "label": "Human Approval"},
    "sub_workflow": {"stage": "branch", "label": "Sub Workflow"},
    "integration_email": {"stage": "action", "label": "Email Action"},
    "integration_slack": {"stage": "notify", "label": "Slack Notify"},
    "integration_notion": {"stage": "action", "label": "Notion Action"},
    "integration_hubspot": {"stage": "action", "label": "HubSpot Action"},
    "integration_zendesk": {"stage": "action", "label": "Zendesk Ticket"},
    "integration_database_write": {"stage": "action", "label": "Database Write"},
}

KEYWORD_MAP: dict[str, list[str]] = {
    "trigger_schedule": ["schedule", "cron", "daily", "weekly", "every"],
    "integration_stripe": ["stripe", "payment received", "charge", "invoice"],
    "integration_gmail": ["email received", "new email", "gmail", "inbox", "mailbox"],
    "integration_http": ["http", "api", "fetch", "request", "enrich"],
    "integration_database": ["database", "knowledge", "rag", "vector", "search", "qdrant"],
    "llm_classify": ["classify", "sentiment", "intent", "score", "triage"],
    "llm_decision": ["decide", "decision", "risk", "priority", "analyze", "analyse"],
    "llm_generate": ["generate", "draft", "write", "reply", "answer", "content", "summarize", "summarise"],
    "condition": ["if", "condition", "branch", "gate", "validate", "check", "refund"],
    "loop": ["loop", "iterate", "batch", "for each", "retry"],
    "human_approval": ["approve", "approval", "manual review", "human review", "confirm"],
    "integration_email": ["reply", "send email", "auto-reply", "respond", "outreach"],
    "integration_slack": ["slack", "notify", "alert", "channel"],
    "integration_notion": ["notion"],
    "integration_hubspot": ["hubspot", "crm", "lead"],
    "integration_google_sheets": ["google sheets", "sheets", "spreadsheet"],
    "integration_zendesk": ["ticket", "zendesk", "support ticket", "case"],
}

AI_KEYWORDS = {"classify", "analyze", "analyse", "summarize", "summarise"}
PREPROCESS_KEYWORDS = {"enrich", "parse", "extract", "fetch", "lookup", "search"}

INTEGRATION_MAPPING_TABLE: dict[str, dict[str, str]] = {
    "email": {"node": "integration_gmail", "action": "email_received"},
    "refund": {"node": "condition", "action": "intent == refund"},
    "ticket": {"node": "integration_zendesk", "action": "zendesk_ticket"},
    "reply": {"node": "integration_email", "action": "auto_reply"},
    "slack": {"node": "integration_slack", "action": "slack_alert"},
    "hubspot": {"node": "integration_hubspot", "action": "hubspot_action"},
    "gmail": {"node": "integration_gmail", "action": "gmail_trigger"},
    "google sheets": {"node": "integration_google_sheets", "action": "google_sheets_action"},
    "stripe": {"node": "integration_stripe", "action": "stripe_trigger"},
}

STAGE_ORDER = ["trigger", "enrich", "process", "branch", "action", "notify"]
STAGE_X = {
    "trigger": 60,
    "enrich": 360,
    "process": 700,
    "branch": 1040,
    "action": 1380,
    "notify": 1720,
}


# ═══════════════════════════════════════════════════════════════════
#  Stage 1: Parser Agent — extracts structured intent from prompt
# ═══════════════════════════════════════════════════════════════════

class PromptParser:
    """Extract trigger, actions, conditions, integrations, ambiguity flags."""

    def parse(self, description: str) -> dict[str, Any]:
        desc = description.lower()
        trigger = self._detect_trigger(desc)
        ai_task = self._detect_ai_task(desc)
        preprocess = self._detect_preprocess(desc)
        conditions = self._detect_conditions(desc)
        actions = self._detect_actions(desc)
        integrations = self._detect_integrations(desc)
        ambiguity = self._detect_ambiguity(trigger, ai_task, conditions, actions)
        confidence = self._compute_confidence(trigger, ai_task, conditions, actions, integrations, ambiguity)

        return {
            "trigger": trigger,
            "preprocess": preprocess,
            "ai_task": ai_task,
            "conditions": conditions,
            "actions": actions,
            "integrations": integrations,
            "ambiguity_flags": ambiguity,
            "confidence": confidence,
        }

    def _detect_trigger(self, desc: str) -> str:
        if any(kw in desc for kw in ["email received", "new email", "gmail", "inbox"]):
            return "email_received"
        if any(kw in desc for kw in ["stripe", "payment received", "charge succeeded"]):
            return "stripe_payment_received"
        if any(kw in desc for kw in ["schedule", "cron", "daily", "weekly"]):
            return "schedule"
        return "webhook_received"

    def _detect_ai_task(self, desc: str) -> str | None:
        if "classify" in desc:
            return "classify_intent"
        if "analyze" in desc or "analyse" in desc or "score" in desc:
            return "analyze_input"
        if "summarize" in desc or "summarise" in desc:
            return "summarize_content"
        return None

    def _detect_preprocess(self, desc: str) -> list[str]:
        steps: list[str] = []
        if "enrich" in desc:
            steps.append("enrichment")
        if any(kw in desc for kw in ["parse", "extract"]):
            steps.append("parsing")
        if any(kw in desc for kw in ["fetch", "lookup", "search"]):
            steps.append("lookup")
        return steps or ["enrichment"]

    def _detect_conditions(self, desc: str) -> list[str]:
        conditions: list[str] = []
        if_clause = re.search(r"\bif\s+([^,.;]+)", desc)
        if if_clause:
            conditions.append(if_clause.group(1).strip())
        amount_condition = re.search(r"amount\s*(>=|<=|>|<|==)\s*(\d+)", desc)
        if amount_condition:
            conditions.append(f"amount {amount_condition.group(1)} {amount_condition.group(2)}")
        if "refund" in desc and not any("refund" in c for c in conditions):
            conditions.append("intent == refund")
        if "approve" in desc or "approval" in desc:
            conditions.append("requires_approval")
        return conditions

    def _detect_actions(self, desc: str) -> list[str]:
        actions: list[str] = []
        for keyword, mapping in INTEGRATION_MAPPING_TABLE.items():
            if keyword in desc:
                actions.append(mapping["action"])
        if "zendesk_ticket" not in actions and "ticket" in desc:
            actions.append("zendesk_ticket")
        return actions or ["notify"]

    def _detect_integrations(self, desc: str) -> list[str]:
        found: list[str] = []
        integration_keywords = {
            "slack": "slack", "gmail": "gmail", "stripe": "stripe",
            "notion": "notion", "hubspot": "hubspot", "zendesk": "zendesk",
            "sheets": "google-sheets", "github": "github", "shopify": "shopify",
        }
        for kw, provider in integration_keywords.items():
            if kw in desc:
                found.append(provider)
        return found

    def _detect_ambiguity(self, trigger: str, ai_task: str | None, conditions: list, actions: list) -> list[str]:
        flags: list[str] = []
        if trigger == "webhook_received" and not ai_task and not conditions and not actions:
            flags.append("no_clear_intent")
        return flags

    def _compute_confidence(
        self, trigger: str, ai_task: str | None, conditions: list,
        actions: list, integrations: list, ambiguity: list,
    ) -> float:
        score = 0.3  # baseline
        if trigger != "webhook_received":
            score += 0.15
        if ai_task:
            score += 0.15
        if conditions:
            score += 0.1
        if len(actions) > 1:
            score += 0.1
        if integrations:
            score += 0.1
        if ambiguity:
            score -= 0.3
        return round(min(max(score, 0.0), 1.0), 2)


# ═══════════════════════════════════════════════════════════════════
#  Stage 2: Planner Agent — converts parsed intent into node plan
# ═══════════════════════════════════════════════════════════════════

class WorkflowPlanner:
    """Convert ParsedIntent into ordered execution plan."""

    def plan(self, description: str, parsed: dict[str, Any]) -> dict[str, Any]:
        desc_lower = description.lower()
        node_types = self._extract_intents(desc_lower, parsed)
        node_types = self._ensure_pipeline(node_types, desc_lower, parsed)
        confidence = self._compute_plan_confidence(node_types, parsed)

        return {
            "node_types": node_types,
            "parsed_intent": parsed,
            "plan_confidence": confidence,
        }

    def _extract_intents(self, desc: str, parsed: dict[str, Any]) -> list[str]:
        scored: list[tuple[str, int]] = []
        for node_type, keywords in KEYWORD_MAP.items():
            score = 0
            for kw in keywords:
                if len(kw) <= 3:
                    if re.search(r"\b" + re.escape(kw) + r"\b", desc):
                        score += 2
                elif kw in desc:
                    score += len(kw)
            if score > 0:
                scored.append((node_type, score))
        for keyword, mapping in INTEGRATION_MAPPING_TABLE.items():
            if keyword in desc:
                scored.append((mapping["node"], 20))
        if parsed:
            trigger = parsed.get("trigger")
            if trigger == "email_received":
                scored.append(("integration_gmail", 30))
            if parsed.get("conditions"):
                scored.append(("condition", 25))
            if parsed.get("actions"):
                for action in parsed["actions"]:
                    if action == "zendesk_ticket":
                        scored.append(("integration_zendesk", 25))
                    if action in {"auto_reply", "email_send"}:
                        scored.append(("integration_email", 25))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [node_type for node_type, _ in scored]

    def _ensure_pipeline(self, node_types: list[str], desc: str, parsed: dict[str, Any]) -> list[str]:
        types = list(node_types)
        stages_present = {NODE_META.get(nt, {}).get("stage") for nt in types}

        if "trigger" not in stages_present:
            types.insert(0, "trigger_webhook")
        if "action" not in stages_present:
            types.append("integration_database_write")
        if "enrich" not in stages_present:
            types.append("integration_http")

        requires_ai = any(kw in desc for kw in AI_KEYWORDS | {"score"})
        has_ai = any(nt.startswith("llm_") for nt in types)
        if requires_ai and not has_ai:
            if "classify" in desc:
                types.append("llm_classify")
            elif "summarize" in desc or "summarise" in desc:
                types.append("llm_generate")
            else:
                types.append("llm_decision")

        if "process" not in {NODE_META.get(nt, {}).get("stage") for nt in types}:
            types.append("llm_generate")
        if "branch" not in stages_present:
            types.append("condition")
        if "notify" not in stages_present:
            types.append("integration_slack")

        # Auto-add human_approval if mentioned
        if any("approv" in kw for kw in (parsed.get("conditions") or [])):
            if "human_approval" not in types:
                types.append("human_approval")

        while len(types) < 6:
            types.append("transform")
        return types

    def _compute_plan_confidence(self, node_types: list[str], parsed: dict[str, Any]) -> float:
        score = parsed.get("confidence", 0.5)
        if len(node_types) >= 4:
            score += 0.1
        if any(nt.startswith("llm_") for nt in node_types):
            score += 0.05
        return round(min(max(score, 0.0), 1.0), 2)


# ═══════════════════════════════════════════════════════════════════
#  Stage 3: Builder Agent — emits final DAG with validation
# ═══════════════════════════════════════════════════════════════════

class WorkflowBuilder:
    """Convert WorkflowPlan into final DAG nodes + edges."""

    def build(self, description: str, plan: dict[str, Any]) -> dict[str, Any]:
        staged = self._stage(plan["node_types"])
        parsed = plan.get("parsed_intent") or {}
        nodes = self._build_nodes(staged, description, parsed)
        edges = self._build_edges(nodes, staged, parsed)
        name = self._workflow_name(description)

        # Validation pass
        validation = self._validate_dag(nodes, edges)
        nodes, edges = self._auto_correct(nodes, edges, validation)

        missing_integrations = self._find_missing_integrations(nodes)
        build_confidence = self._compute_build_confidence(nodes, edges, validation, plan)

        return {
            "name": name,
            "nodes": nodes,
            "edges": edges,
            "explanation": self._generate_explanation(description, nodes, edges),
            "missing_integrations": missing_integrations,
            "confidence": build_confidence,
            "needs_confirmation": build_confidence < 0.6,
            "plan_confidence": plan.get("plan_confidence", 0.5),
            "parse_confidence": parsed.get("confidence", 0.5),
        }

    def _stage(self, node_types: list[str]) -> dict[str, list[str]]:
        staged = {stage: [] for stage in STAGE_ORDER}
        for nt in node_types:
            stage = NODE_META.get(nt, {}).get("stage", "process")
            staged[stage].append(nt)
        return staged

    def _build_nodes(self, staged: dict[str, list[str]], desc: str, parsed: dict[str, Any]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        counter = 1
        previous_id = "input"
        explicit_condition = parsed["conditions"][0] if parsed.get("conditions") else None

        for stage in STAGE_ORDER:
            for idx, node_type in enumerate(staged[stage]):
                node_id = str(counter)
                y = int(220 + (idx - (len(staged[stage]) - 1) / 2) * 170)
                config = self._node_config(node_type, desc, previous_id, explicit_condition)
                nodes.append({
                    "id": node_id,
                    "type": node_type,
                    "name": NODE_META.get(node_type, {}).get("label", node_type),
                    "position": {"x": STAGE_X[stage], "y": y},
                    "config": config,
                    "ai_brain": node_type.startswith("llm_"),
                    "memory": "short_term" if node_type.startswith("llm_") else None,
                    "retry_policy": {
                        "max_retries": 2,
                        "backoff": "exponential",
                        "retry_on": ["timeout", "api_error"],
                    },
                    "timeout_ms": 30000 if node_type.startswith("llm_") else 10000,
                    "input_mapping": {},
                    "output_mapping": {},
                    "on_error": {"strategy": "retry_then_fallback", "max_retries": 2},
                })
                previous_id = node_id
                counter += 1
        return nodes

    def _node_config(self, node_type: str, desc: str, prev_id: str, explicit_condition: str | None = None) -> dict[str, Any]:
        ref = "{{" + prev_id + ".output}}"
        configs: dict[str, dict[str, Any]] = {
            "trigger_webhook": {"path": "/webhooks/generated-workflow"},
            "trigger_schedule": {"cron": "0 9 * * *"},
            "integration_stripe": {"action": "payment_received"},
            "integration_http": {"action": "fetch", "url": "https://api.example.com/data", "input": ref},
            "integration_database": {"action": "search", "query": ref, "top_k": 5},
            "llm_classify": {"prompt": f"Classify and score: {desc}", "input": ref},
            "llm_decision": {"prompt": f"Make routing decision for: {desc}", "input": ref},
            "llm_generate": {"prompt": f"Generate best output for: {desc}", "input": ref},
            "condition": {"expression": explicit_condition or "True"},
            "loop": {"items_path": "items"},
            "transform": {"template": "{{input}}"},
            "human_approval": {"message": "Manual approval required for this step."},
            "sub_workflow": {"workflow_id": ""},
            "integration_email": {"action": "send_email", "body": ref},
            "integration_gmail": {"action": "new_message", "folder": "INBOX"},
            "integration_slack": {"action": "send_message", "message": ref},
            "integration_notion": {"action": "create_page", "content": ref},
            "integration_hubspot": {"action": "create_or_update_contact", "payload": ref},
            "integration_google_sheets": {"action": "append_row", "payload": ref},
            "integration_zendesk": {"action": "create_ticket", "payload": ref},
            "integration_database_write": {"action": "upsert_record", "payload": ref},
        }
        return configs.get(node_type, {"input": ref})

    def _build_edges(self, nodes: list[dict[str, Any]], staged: dict[str, list[str]], parsed: dict[str, Any]) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        by_stage: dict[str, list[str]] = {stage: [] for stage in STAGE_ORDER}
        for node in nodes:
            stage = NODE_META.get(node["type"], {}).get("stage", "process")
            by_stage[stage].append(node["id"])

        edge_counter = 1
        previous_stage_nodes: list[str] = []
        for stage in STAGE_ORDER:
            current = by_stage[stage]
            if not current:
                continue
            if previous_stage_nodes:
                if len(previous_stage_nodes) == 1 and len(current) == 1:
                    edges.append(self._edge(edge_counter, previous_stage_nodes[0], current[0]))
                    edge_counter += 1
                elif len(previous_stage_nodes) == 1:
                    for target in current:
                        edges.append(self._edge(edge_counter, previous_stage_nodes[0], target))
                        edge_counter += 1
                elif len(current) == 1:
                    for source in previous_stage_nodes:
                        edges.append(self._edge(edge_counter, source, current[0]))
                        edge_counter += 1
                else:
                    for target in current:
                        edges.append(self._edge(edge_counter, previous_stage_nodes[-1], target))
                        edge_counter += 1
            previous_stage_nodes = current

        # Condition branching
        condition_nodes = [n["id"] for n in nodes if n["type"] == "condition"]
        action_nodes = by_stage.get("action", [])
        notify_nodes = by_stage.get("notify", [])
        for cond_id in condition_nodes:
            if action_nodes:
                edges.append(self._edge(edge_counter, cond_id, action_nodes[0], "result['result'] == True"))
                edge_counter += 1
            false_target = notify_nodes[0] if notify_nodes else None
            if false_target:
                edges.append(self._edge(edge_counter, cond_id, false_target, "result['result'] == False"))
                edge_counter += 1

        # Loop feeds process
        loop_nodes = [n["id"] for n in nodes if n["type"] == "loop"]
        process_nodes = by_stage.get("process", [])
        for loop_id in loop_nodes:
            if process_nodes:
                edges.append(self._edge(edge_counter, loop_id, process_nodes[0]))
                edge_counter += 1

        # Deduplicate
        unique: set[tuple[str, str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for edge in edges:
            key = (edge["source"], edge["target"], edge["condition"])
            if key not in unique:
                unique.add(key)
                deduped.append(edge)
        return deduped

    def _edge(self, counter: int, source: str, target: str, condition: str = "true") -> dict[str, Any]:
        return {"id": f"edge-{counter}", "source": source, "target": target, "condition": condition}

    def _validate_dag(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
        node_ids = {n["id"] for n in nodes}
        issues: list[str] = []
        for edge in edges:
            if edge["source"] not in node_ids:
                issues.append(f"Edge {edge['id']} has invalid source {edge['source']}")
            if edge["target"] not in node_ids:
                issues.append(f"Edge {edge['id']} has invalid target {edge['target']}")
        targets = {e["target"] for e in edges}
        orphans = [n["id"] for n in nodes if n["id"] not in targets and NODE_META.get(n["type"], {}).get("stage") != "trigger"]
        if orphans:
            issues.append(f"Orphan nodes with no incoming edges: {orphans}")
        return {"valid": len(issues) == 0, "issues": issues}

    def _auto_correct(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]], validation: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        # Remove edges pointing to non-existent nodes
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in node_ids and e["target"] in node_ids]
        return nodes, edges

    def _find_missing_integrations(self, nodes: list[dict[str, Any]]) -> list[str]:
        missing: list[str] = []
        for node in nodes:
            if node["type"].startswith("integration_"):
                provider = node["type"].replace("integration_", "")
                if provider not in {"http", "database", "database_write", "email", "log_fetch", "document_parser", "enrichment_api", "accounting", "inventory"}:
                    missing.append(provider)
        return missing

    def _compute_build_confidence(self, nodes: list, edges: list, validation: dict, plan: dict) -> float:
        score = plan.get("plan_confidence", 0.5)
        if validation["valid"]:
            score += 0.1
        else:
            score -= 0.2
        if len(nodes) >= 4 and len(edges) >= 3:
            score += 0.1
        return round(min(max(score, 0.0), 1.0), 2)

    def _generate_explanation(self, desc: str, nodes: list, edges: list) -> str:
        node_summary = ", ".join(n["name"] for n in nodes[:6])
        return f"Generated {len(nodes)}-node workflow with {len(edges)} connections: {node_summary}. Based on prompt: \"{desc[:100]}...\""

    def _workflow_name(self, desc: str) -> str:
        d = desc.lower()
        if "support" in d:
            return "Support Triage Automation"
        if "lead" in d:
            return "Lead Qualification Workflow"
        if "payment" in d or "fraud" in d:
            return "Payment Risk Workflow"
        if "social" in d:
            return "Social Content Workflow"
        if "knowledge" in d or "rag" in d:
            return "Knowledge Assistant Workflow"
        if "invoice" in d:
            return "Invoice Processing Workflow"
        if "approval" in d:
            return "Approval Workflow"
        return "Generated Workflow"


# ═══════════════════════════════════════════════════════════════════
#  Orchestrator — runs all 3 stages
# ═══════════════════════════════════════════════════════════════════

class AuraFlowWorkflowArchitect:
    """3-stage pipeline: Parser → Planner → Builder with confidence scoring."""

    def __init__(self) -> None:
        self.parser = PromptParser()
        self.planner = WorkflowPlanner()
        self.builder = WorkflowBuilder()

    def generate(self, description: str) -> dict[str, Any]:
        desc = description.strip()
        if not desc:
            raise ValueError("Prompt is required.")

        # Stage 1: Parse
        parsed = self.parser.parse(desc)

        # Check if clarification needed
        if parsed["confidence"] < 0.3 and parsed.get("ambiguity_flags"):
            raise ValueError("clarification_required")

        # Stage 2: Plan
        plan = self.planner.plan(desc, parsed)

        # Stage 3: Build
        result = self.builder.build(desc, plan)

        # Return with all confidence data
        return result


workflow_architect_service = AuraFlowWorkflowArchitect()
