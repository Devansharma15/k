from fastapi import APIRouter

from .data import ACTIVITIES, APPS, WORKFLOWS

router = APIRouter()


@router.get("/overview")
async def get_overview():
    active_workflows = sum(1 for workflow in WORKFLOWS if workflow["status"] == "Active")

    return {
        "product": {
            "name": "AuraFlow",
            "tagline": "Orchestrate apps, workflows, and retrieval in one control room.",
        },
        "stats": [
            {
                "name": "Total Apps",
                "value": str(len(APPS)),
                "trend": "2 ready for production",
                "icon": "Cpu",
                "tone": "sky",
            },
            {
                "name": "Active Workflows",
                "value": str(active_workflows),
                "trend": "1 draft needs review",
                "icon": "Zap",
                "tone": "amber",
            },
            {
                "name": "Runs Today",
                "value": str(sum(workflow["runs_today"] for workflow in WORKFLOWS)),
                "trend": "Healthy execution volume",
                "icon": "Activity",
                "tone": "emerald",
            },
            {
                "name": "Median Latency",
                "value": f'{round(sum(workflow["latency_ms"] for workflow in WORKFLOWS) / len(WORKFLOWS))}ms',
                "trend": "Across active flows",
                "icon": "Gauge",
                "tone": "rose",
            },
        ],
        "apps": APPS,
        "workflows": WORKFLOWS,
        "activities": ACTIVITIES,
    }
