from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class App(BaseModel):
    id: str
    name: str
    description: str
    status: str
    icon: str

@router.get("/apps")
async def get_apps():
    return [
        {
            "id": "1",
            "name": "Customer Support Bot",
            "description": "AI agent for handling Q&A based on documentation.",
            "status": "Ready",
            "icon": "Cpu",
        },
        {
            "id": "2",
            "name": "Lead Generator",
            "description": "Extracts leads from unstructured text.",
            "status": "Indexing",
            "icon": "Zap",
        }
    ]
