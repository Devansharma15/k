APPS = [
    {
        "id": "1",
        "name": "Customer Support Bot",
        "description": "Answers customer questions with retrieval over product documentation.",
        "status": "Ready",
        "icon": "Cpu",
    },
    {
        "id": "2",
        "name": "Lead Generator",
        "description": "Extracts qualified leads from unstructured notes and web research.",
        "status": "Indexing",
        "icon": "Zap",
    },
    {
        "id": "3",
        "name": "Ops Copilot",
        "description": "Summarizes incidents, logs, and deployment updates for the team.",
        "status": "Ready",
        "icon": "Shield",
    },
]

WORKFLOWS = [
    {
        "id": "wf-1",
        "name": "Lead Qualification",
        "status": "Active",
        "runs_today": 28,
        "latency_ms": 142,
    },
    {
        "id": "wf-2",
        "name": "Support Escalation",
        "status": "Draft",
        "runs_today": 9,
        "latency_ms": 214,
    },
]

ACTIVITIES = [
    {
        "id": "act-1",
        "type": "app",
        "name": "Customer Support Bot",
        "action": "served 124 resolved conversations",
        "time": "2 hours ago",
    },
    {
        "id": "act-2",
        "type": "workflow",
        "name": "Lead Qualification",
        "action": "processed a new inbound batch",
        "time": "45 minutes ago",
    },
    {
        "id": "act-3",
        "type": "model",
        "name": "Ops Copilot",
        "action": "refreshed its knowledge base",
        "time": "Today",
    },
]
