from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.workflow_architect_service import workflow_architect_service
from ..services.workflow_platform_service import WorkflowLockedError, workflow_platform_service

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
    except WorkflowLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
    except WorkflowLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/platform/{workflow_id}/rollback/{version_id}")
async def rollback_workflow(workflow_id: str, version_id: str):
    try:
        return workflow_platform_service.rollback_workflow(workflow_id, version_id)
    except WorkflowLockedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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


@router.get("/workflows/platform/{workflow_id}/runs/{run_id}/logs")
async def get_run_logs(workflow_id: str, run_id: str):
    try:
        return workflow_platform_service.get_run_logs(workflow_id, run_id)
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
    try:
        return workflow_architect_service.generate(request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
