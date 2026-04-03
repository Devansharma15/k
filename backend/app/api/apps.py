from fastapi import APIRouter

from .data import APPS

router = APIRouter()

@router.get("/apps")
async def get_apps():
    return APPS
