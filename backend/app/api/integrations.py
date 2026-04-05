import json

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from ..services.integrations_service import (
    IntegrationAuthError,
    IntegrationConfigError,
    IntegrationRateLimitError,
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
    try:
        return integrations_service.get_integrations(user_id=user_id)
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


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
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except IntegrationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/integrations/save-api-key")
async def save_api_key(request: ApiKeyConnectRequest):
    try:
        return integrations_service.save_api_key(
            provider=request.provider,
            api_key=request.api_key,
            user_id=request.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
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
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except IntegrationRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except IntegrationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/integrations/create-session")
async def create_session(request: OAuthConnectRequest):
    try:
        return integrations_service.create_connect_session(
            provider=request.provider,
            user_id=request.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except IntegrationRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except IntegrationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/integrations/status")
async def get_integration_status(provider: str, user_id: str = "demo-user"):
    try:
        return integrations_service.get_connection_status(provider, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/integrations/webhook")
async def integrations_webhook(
    request: Request,
    x_nango_signature: str | None = Header(default=None),
):
    try:
        raw_body = await request.body()
        payload = json.loads(raw_body.decode("utf-8"))
        return integrations_service.handle_nango_webhook(
            payload,
            x_nango_signature,
            raw_body=raw_body,
        )
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload.") from exc
    except IntegrationConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/integrations/{provider}")
async def disconnect_integration(provider: str, user_id: str = "demo-user"):
    try:
        return integrations_service.disconnect_integration(provider, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrationAuthError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
