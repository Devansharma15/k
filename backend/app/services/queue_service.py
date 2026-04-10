import json
from typing import Any
from app.services.redis_client import redis_client

WORKFLOW_QUEUE_NAME = "workflow_queue"

def enqueue_workflow(run_id: str, workflow_id: str, snapshot: dict[str, Any], context: dict[str, Any], mode: str, debug: bool):
    """
    Enqueue a workflow run payload onto the Upstash Redis queue using LPUSH.
    """
    payload = {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "snapshot": snapshot,
        "context": context,
        "mode": mode,
        "debug": debug
    }
    redis_client.lpush(WORKFLOW_QUEUE_NAME, json.dumps(payload))
