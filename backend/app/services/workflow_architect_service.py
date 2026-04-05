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
    "integration_email": ["reply", "send email", "auto-reply", "respond", "outreach"],
    "integration_slack": ["slack", "notify", "alert", "channel"],
    "integration_notion": ["notion"],
    "integration_hubspot": ["hubspot", "crm", "lead"],
    "integration_google_sheets": ["google sheets", "sheets", "spreadsheet"],
    "integration_zendesk": ["ticket", "zendesk", "support ticket", "case"],
}

AI_KEYWORDS = {"classify", "analyze", "analyse", "summarize", "summarise"}
PREPROCESS_KEYWORDS = {"enrich", "parse", "extract", "fetch", "lookup", "search"}
ACTION_KEYWORDS = {
    "slack",
    "hubspot",
    "gmail",
    "zendesk",
    "notion",
    "google sheets",
    "sheets",
    "email",
    "reply",
}

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


class AuraFlowWorkflowArchitect:
    """
    Self-contained workflow architect:
    - no external API dependencies
    - instruction-aware keyword -> node mapping
    - non-linear DAG with condition/switch-like branching and loop patterns
    - dynamic variable interpolation in configs
    """

    def generate(self, description: str) -> dict[str, Any]:
        desc = description.strip()
        if not desc:
            raise ValueError("Prompt is required.")
        structure = self._extract_prompt_structure(desc)
        if self._requires_clarification(structure):
            raise ValueError("clarification_required")
        return self._generate_local(desc, structure)

    def _generate_local(self, description: str, structure: dict[str, Any] | None = None) -> dict[str, Any]:
        desc = description.strip()
        desc_lower = desc.lower()

        node_types = self._extract_intents(desc_lower, structure)
        node_types = self._ensure_pipeline(node_types, desc_lower, structure)
        staged = self._stage(node_types)
        nodes = self._build_nodes(staged, desc, structure)
        edges = self._build_edges(nodes, staged, structure)
        name = self._workflow_name(desc)
        payload = {"name": name, "nodes": nodes, "edges": edges}
        if structure:
            payload["structure"] = structure
        return payload

    def _extract_prompt_structure(self, description: str) -> dict[str, Any]:
        desc = description.lower()
        trigger = "webhook_received"
        if any(keyword in desc for keyword in ["email received", "new email", "gmail", "inbox"]):
            trigger = "email_received"
        elif any(keyword in desc for keyword in ["stripe", "payment received", "charge succeeded"]):
            trigger = "stripe_payment_received"
        elif any(keyword in desc for keyword in ["schedule", "cron", "daily", "weekly"]):
            trigger = "schedule"

        ai_task = None
        if "classify" in desc:
            ai_task = "classify_intent"
        elif "analyze" in desc or "analyse" in desc or "score" in desc:
            ai_task = "analyze_input"
        elif "summarize" in desc or "summarise" in desc:
            ai_task = "summarize_content"

        preprocess_steps: list[str] = []
        if any(keyword in desc for keyword in PREPROCESS_KEYWORDS):
            if "enrich" in desc:
                preprocess_steps.append("enrichment")
            if any(keyword in desc for keyword in ["parse", "extract"]):
                preprocess_steps.append("parsing")
            if any(keyword in desc for keyword in ["fetch", "lookup", "search"]):
                preprocess_steps.append("lookup")
        if not preprocess_steps:
            preprocess_steps.append("enrichment")

        conditions: list[str] = []
        if_clause = re.search(r"\bif\s+([^,.;]+)", desc)
        if if_clause:
            conditions.append(if_clause.group(1).strip())
        amount_condition = re.search(r"amount\s*(>=|<=|>|<|==)\s*(\d+)", desc)
        if amount_condition:
            conditions.append(
                f"amount {amount_condition.group(1)} {amount_condition.group(2)}"
            )
        if "refund" in desc and not any("refund" in condition for condition in conditions):
            conditions.append("intent == refund")

        matched_actions: list[str] = []
        for keyword, mapping in INTEGRATION_MAPPING_TABLE.items():
            if keyword in desc:
                matched_actions.append(mapping["action"])
        if "zendesk_ticket" not in matched_actions and "ticket" in desc:
            matched_actions.append("zendesk_ticket")
        actions = list(matched_actions)
        if not actions:
            actions.append("notify")

        return {
            "trigger": trigger,
            "preprocess": preprocess_steps,
            "ai_task": ai_task,
            "conditions": conditions,
            "actions": actions,
            "matched_actions": matched_actions,
        }

    def _requires_clarification(self, structure: dict[str, Any]) -> bool:
        return (
            structure.get("trigger") == "webhook_received"
            and not structure.get("ai_task")
            and not structure.get("conditions")
            and not structure.get("matched_actions")
        )

    def _extract_intents(self, desc: str, structure: dict[str, Any] | None = None) -> list[str]:
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
        if structure:
            trigger = structure.get("trigger")
            if trigger == "email_received":
                scored.append(("integration_gmail", 30))
            if structure.get("conditions"):
                scored.append(("condition", 25))
            if structure.get("actions"):
                for action in structure["actions"]:
                    if action == "zendesk_ticket":
                        scored.append(("integration_zendesk", 25))
                    if action in {"auto_reply", "email_send"}:
                        scored.append(("integration_email", 25))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [node_type for node_type, _ in scored]

    def _ensure_pipeline(
        self,
        node_types: list[str],
        desc: str,
        structure: dict[str, Any] | None = None,
    ) -> list[str]:
        types = list(node_types)
        stages_present = {NODE_META.get(node_type, {}).get("stage") for node_type in types}

        # Force multi-step structure: always include at least one trigger and one action.
        if "trigger" not in stages_present:
            types.insert(0, "trigger_webhook")
        if "action" not in stages_present:
            types.append("integration_database_write")

        if "enrich" not in stages_present:
            types.append("integration_http")

        if structure and structure.get("preprocess"):
            if "integration_http" not in types:
                types.append("integration_http")

        # Auto add AI node for classify/analyze/summarize prompts.
        requires_ai = any(keyword in desc for keyword in AI_KEYWORDS | {"score"})
        has_ai = any(node_type.startswith("llm_") for node_type in types)
        if requires_ai and not has_ai:
            if "classify" in desc:
                types.append("llm_classify")
            elif "summarize" in desc or "summarise" in desc:
                types.append("llm_generate")
            else:
                types.append("llm_decision")

        if "process" not in {NODE_META.get(node_type, {}).get("stage") for node_type in types}:
            types.append("llm_generate")
        if "branch" not in stages_present:
            types.append("condition")
        if "notify" not in stages_present:
            types.append("integration_slack")

        # Keep meaningful complexity by enforcing at least 6 nodes.
        while len(types) < 6:
            types.append("transform")
        return types

    def _stage(self, node_types: list[str]) -> dict[str, list[str]]:
        staged = {stage: [] for stage in STAGE_ORDER}
        for node_type in node_types:
            stage = NODE_META.get(node_type, {}).get("stage", "process")
            staged[stage].append(node_type)
        return staged

    def _build_nodes(
        self,
        staged: dict[str, list[str]],
        desc: str,
        structure: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        counter = 1
        previous_id = "input"
        explicit_condition = structure["conditions"][0] if structure and structure.get("conditions") else None

        for stage in STAGE_ORDER:
            for idx, node_type in enumerate(staged[stage]):
                node_id = str(counter)
                y = int(220 + (idx - (len(staged[stage]) - 1) / 2) * 170)
                config = self._node_config(node_type, desc, previous_id, explicit_condition)
                nodes.append(
                    {
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
                    }
                )
                previous_id = node_id
                counter += 1
        return nodes

    def _node_config(
        self,
        node_type: str,
        desc: str,
        prev_id: str,
        explicit_condition: str | None = None,
    ) -> dict[str, Any]:
        ref = "{{" + prev_id + ".output}}"
        if node_type == "trigger_webhook":
            return {"path": "/webhooks/generated-workflow"}
        if node_type == "trigger_schedule":
            return {"cron": "0 9 * * *"}
        if node_type == "integration_stripe":
            return {"action": "payment_received"}
        if node_type == "integration_http":
            return {"action": "fetch", "url": "https://api.example.com/data", "input": ref}
        if node_type == "integration_database":
            return {"action": "search", "query": ref, "top_k": 5}
        if node_type == "llm_classify":
            return {"prompt": f"Classify and score: {desc}", "input": ref, "provider": "local"}
        if node_type == "llm_decision":
            return {"prompt": f"Make routing decision for: {desc}", "input": ref, "provider": "local"}
        if node_type == "llm_generate":
            return {"prompt": f"Generate best output for: {desc}", "input": ref, "provider": "local"}
        if node_type == "condition":
            return {"expression": explicit_condition or "True"}
        if node_type == "loop":
            return {"items_path": "items"}
        if node_type == "transform":
            return {"template": "{{input}}"}
        if node_type == "integration_email":
            return {"action": "send_email", "body": ref}
        if node_type == "integration_gmail":
            return {"action": "new_message", "folder": "INBOX"}
        if node_type == "integration_slack":
            return {"action": "send_message", "message": ref}
        if node_type == "integration_notion":
            return {"action": "create_page", "content": ref}
        if node_type == "integration_hubspot":
            return {"action": "create_or_update_contact", "payload": ref}
        if node_type == "integration_google_sheets":
            return {"action": "append_row", "payload": ref}
        if node_type == "integration_zendesk":
            return {"action": "create_ticket", "payload": ref}
        if node_type == "integration_database_write":
            return {"action": "upsert_record", "payload": ref}
        return {"input": ref}

    def _build_edges(
        self,
        nodes: list[dict[str, Any]],
        staged: dict[str, list[str]],
        structure: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
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

        # Non-linear branch behavior for condition nodes.
        condition_nodes = [node["id"] for node in nodes if node["type"] == "condition"]
        action_nodes = by_stage.get("action", [])
        notify_nodes = by_stage.get("notify", [])
        action_hints = structure.get("actions", []) if structure else []
        for cond_id in condition_nodes:
            if action_nodes:
                edges.append(
                    self._edge(edge_counter, cond_id, action_nodes[0], "result.get('result') == True")
                )
                edge_counter += 1
            false_target = notify_nodes[0] if notify_nodes else None
            if len(action_nodes) > 1 and any("google_sheets" in action for action in action_hints):
                false_target = action_nodes[-1]
            if false_target:
                edges.append(
                    self._edge(edge_counter, cond_id, false_target, "result.get('result') == False")
                )
                edge_counter += 1

        # Loop pattern: loop node feeds first process node.
        loop_nodes = [node["id"] for node in nodes if node["type"] == "loop"]
        process_nodes = by_stage.get("process", [])
        for loop_id in loop_nodes:
            if process_nodes:
                edges.append(self._edge(edge_counter, loop_id, process_nodes[0]))
                edge_counter += 1

        # Deduplicate by (source,target,condition)
        unique: set[tuple[str, str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for edge in edges:
            key = (edge["source"], edge["target"], edge["condition"])
            if key in unique:
                continue
            unique.add(key)
            deduped.append(edge)
        return deduped

    def _edge(self, edge_counter: int, source: str, target: str, condition: str = "true") -> dict[str, Any]:
        return {
            "id": f"edge-{edge_counter}",
            "source": source,
            "target": target,
            "condition": condition,
        }

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
        return "Generated Workflow"


workflow_architect_service = AuraFlowWorkflowArchitect()
