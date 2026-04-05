from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.integrations_service import (
    IntegrationConfigError,
    integrations_service,
)

router = APIRouter()


class ApiKeyConnectRequest(BaseModel):
    provider: str
    api_key: str = Field(min_length=1)
    user_id: str = "demo-user"


class OAuthConnectRequest(BaseModel):
    provider: str
    user_id: str = "demo-user"


class EnvDetectRequest(BaseModel):
    provider: str


@router.get("/integrations")
async def get_integrations(user_id: str = "demo-user"):
    return integrations_service.get_integrations(user_id=user_id)


@router.post("/connect/env-detect")
async def detect_env(request: EnvDetectRequest):
    try:
        return integrations_service.detect_env_key(request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/connect/api-key")
async def connect_api_key(request: ApiKeyConnectRequest):
    try:
        return integrations_service.connect_api_key(
            provider=request.provider,
            api_key=request.api_key,
            user_id=request.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/connect/oauth")
async def connect_oauth(request: OAuthConnectRequest):
    try:
        return integrations_service.connect_oauth(
            provider=request.provider,
            user_id=request.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
