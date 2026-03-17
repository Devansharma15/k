from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

class WorkflowRun(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

@router.post("/workflow/run")
async def run_workflow(workflow: WorkflowRun):
    # Mock sequential execution
    results = []
    for node in workflow.nodes:
        results.append({
            "node_id": node.get("id"),
            "status": "Success",
            "output": f"Executed {node.get('type')} logic successfully."
        })
    
    return {
        "status": "Completed",
        "results": results,
        "final_output": "Workflow completed simulation successfully."
    }
