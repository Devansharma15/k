from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.workflow_platform_service import workflow_platform_service

router = APIRouter()


class WorkflowSaveRequest(BaseModel):
    name: str
    snapshot: dict[str, Any]


class WorkflowRunRequest(BaseModel):
    mode: str
    debug: bool = False
    input: dict[str, Any] = Field(default_factory=dict)
    version_id: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: str


class GenerateWorkflowRequest(BaseModel):
    prompt: str = Field(min_length=1)


@router.get("/workflows/platform")
async def list_workflows():
    return workflow_platform_service.list_workflows()


@router.post("/workflows/platform")
async def create_workflow(request: WorkflowSaveRequest):
    try:
        workflow_platform_service.validate_snapshot(request.snapshot)
        return workflow_platform_service.create_workflow(request.name, request.snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workflows/platform/{workflow_id}")
async def get_workflow(workflow_id: str):
    try:
        return workflow_platform_service.get_workflow(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/platform/{workflow_id}")
async def update_workflow(workflow_id: str, request: WorkflowSaveRequest):
    try:
        return workflow_platform_service.update_workflow(
            workflow_id,
            request.name,
            request.snapshot,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/platform/{workflow_id}/validate")
async def validate_workflow(workflow_id: str, request: WorkflowSaveRequest):
    try:
        return workflow_platform_service.validate_snapshot(request.snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/platform/{workflow_id}/publish")
async def publish_workflow(workflow_id: str):
    try:
        return workflow_platform_service.publish_workflow(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/platform/{workflow_id}/rollback/{version_id}")
async def rollback_workflow(workflow_id: str, version_id: str):
    try:
        return workflow_platform_service.rollback_workflow(workflow_id, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/platform/{workflow_id}/run")
async def run_workflow(workflow_id: str, request: WorkflowRunRequest):
    try:
        return workflow_platform_service.run_workflow(
            workflow_id=workflow_id,
            mode=request.mode,
            debug=request.debug,
            input_data=request.input,
            version_id=request.version_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workflows/platform/{workflow_id}/runs")
async def list_runs(workflow_id: str):
    return workflow_platform_service.list_runs(workflow_id)


@router.get("/workflows/platform/{workflow_id}/runs/{run_id}")
async def get_run(workflow_id: str, run_id: str):
    try:
        return workflow_platform_service.get_run(workflow_id, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workflows/platform/{workflow_id}/versions")
async def list_versions(workflow_id: str):
    return workflow_platform_service.list_versions(workflow_id)


@router.get("/node-types")
async def list_node_types():
    return workflow_platform_service.list_node_types()


@router.get("/templates")
async def list_templates():
    return workflow_platform_service.list_templates()


@router.post("/templates/{template_id}/instantiate")
async def instantiate_template(template_id: str):
    try:
        return workflow_platform_service.instantiate_template(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/approvals")
async def list_approvals():
    return workflow_platform_service.list_approvals()


@router.post("/approvals/{approval_id}/decision")
async def decide_approval(approval_id: str, request: ApprovalDecisionRequest):
    try:
        return workflow_platform_service.decide_approval(approval_id, request.decision)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/usage/llm")
async def get_llm_usage():
    return workflow_platform_service.get_llm_usage()


@router.post("/generate-workflow")
async def generate_workflow(request: GenerateWorkflowRequest):
    prompt = request.prompt.lower()
    nodes = [
        {
            "id": "trigger-1",
            "type": "trigger_webhook",
            "name": "Generated Trigger",
            "position": {"x": 100, "y": 160},
            "config": {"path": "/webhooks/generated"},
            "ai_brain": False,
            "memory": None,
            "retry_policy": {"max_retries": 0, "backoff": "none", "retry_on": []},
            "timeout_ms": 5000,
        }
    ]
    edges = []
    cursor_x = 380

    if "stripe" in prompt:
        nodes.append(
            {
                "id": "stripe-action",
                "type": "integration_stripe",
                "name": "Stripe Event",
                "position": {"x": cursor_x, "y": 160},
                "config": {"action": "handle_event"},
                "ai_brain": False,
                "memory": None,
                "retry_policy": {"max_retries": 1, "backoff": "exponential", "retry_on": ["api_error"]},
                "timeout_ms": 10000,
            }
        )
        edges.append({"id": "e-trigger-stripe", "source": "trigger-1", "target": "stripe-action", "condition": "true"})
        cursor_x += 280

    if "if " in prompt or "amount >" in prompt:
        nodes.append(
            {
                "id": "condition-1",
                "type": "condition",
                "name": "Condition Check",
                "position": {"x": cursor_x, "y": 160},
                "config": {"expression": "True"},
                "ai_brain": False,
                "memory": None,
                "retry_policy": {"max_retries": 0, "backoff": "none", "retry_on": []},
                "timeout_ms": 5000,
            }
        )
        source = nodes[-2]["id"] if len(nodes) > 1 else "trigger-1"
        edges.append({"id": "e-prev-condition", "source": source, "target": "condition-1", "condition": "true"})
        cursor_x += 280

    if "slack" in prompt:
        nodes.append(
            {
                "id": "slack-action",
                "type": "integration_slack",
                "name": "Slack Send Message",
                "position": {"x": cursor_x, "y": 120},
                "config": {"action": "send_message"},
                "ai_brain": False,
                "memory": None,
                "retry_policy": {"max_retries": 2, "backoff": "exponential", "retry_on": ["api_error"]},
                "timeout_ms": 10000,
            }
        )
        source = "condition-1" if any(node["id"] == "condition-1" for node in nodes) else nodes[-2]["id"]
        edges.append({"id": "e-to-slack", "source": source, "target": "slack-action", "condition": "true"})

    if "notion" in prompt:
        nodes.append(
            {
                "id": "notion-action",
                "type": "integration_notion",
                "name": "Notion Create Page",
                "position": {"x": cursor_x, "y": 260},
                "config": {"action": "create_page"},
                "ai_brain": False,
                "memory": None,
                "retry_policy": {"max_retries": 2, "backoff": "exponential", "retry_on": ["api_error"]},
                "timeout_ms": 10000,
            }
        )
        source = "condition-1" if any(node["id"] == "condition-1" for node in nodes) else nodes[-2]["id"]
        edges.append({"id": "e-to-notion", "source": source, "target": "notion-action", "condition": "true"})

    if len(nodes) == 1:
        nodes.append(
            {
                "id": "llm-action",
                "type": "llm_generate",
                "name": "LLM Generate",
                "position": {"x": 380, "y": 160},
                "config": {"prompt": request.prompt, "memory": "short_term"},
                "ai_brain": True,
                "memory": "short_term",
                "retry_policy": {"max_retries": 1, "backoff": "exponential", "retry_on": ["rate_limit"]},
                "timeout_ms": 30000,
            }
        )
        edges.append({"id": "e-trigger-llm", "source": "trigger-1", "target": "llm-action", "condition": "true"})

    return {"name": "Generated Workflow", "nodes": nodes, "edges": edges}
