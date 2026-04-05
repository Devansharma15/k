from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..services.knowledge_base_service import (
    DEFAULT_USER_ID,
    KnowledgeBaseConfigError,
    knowledge_base_service,
)

router = APIRouter()


class QueryRequest(BaseModel):
    dataset_id: str
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


@router.get("/knowledge-base/datasets")
async def get_datasets(user_id: str = DEFAULT_USER_ID):
    return knowledge_base_service.list_datasets(user_id=user_id)


@router.get("/knowledge-base/datasets/{dataset_id}/documents")
async def get_documents(
    dataset_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = DEFAULT_USER_ID,
):
    try:
        return knowledge_base_service.list_documents(
            dataset_id=dataset_id,
            page=page,
            limit=limit,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/knowledge-base/datasets/{dataset_id}/upload")
async def upload_document(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = DEFAULT_USER_ID,
):
    try:
        content = await file.read()
        result = knowledge_base_service.create_upload_record(
            dataset_id=dataset_id,
            file_name=file.filename or "upload.pdf",
            content=content,
            mime_type=file.content_type or "application/pdf",
            user_id=user_id,
        )
        if not result["duplicate"]:
            background_tasks.add_task(
                knowledge_base_service.ingest_document,
                result["document_id"],
            )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/knowledge-base/datasets/{dataset_id}/documents/{document_id}/file")
async def get_document_file(
    dataset_id: str,
    document_id: str,
    user_id: str = DEFAULT_USER_ID,
):
    try:
        path = knowledge_base_service.get_document_file_path(
            dataset_id=dataset_id,
            document_id=document_id,
            user_id=user_id,
        )
        return FileResponse(path, media_type="application/pdf", filename=path.name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/knowledge-base/datasets/{dataset_id}/documents/{document_id}")
async def delete_document(
    dataset_id: str,
    document_id: str,
    user_id: str = DEFAULT_USER_ID,
):
    try:
        return knowledge_base_service.delete_document(
            dataset_id=dataset_id,
            document_id=document_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/knowledge-base/query")
async def query_knowledge_base(
    request: QueryRequest,
    user_id: str = DEFAULT_USER_ID,
):
    try:
        return knowledge_base_service.query_dataset(
            dataset_id=request.dataset_id,
            query=request.query,
            top_k=request.top_k,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KnowledgeBaseConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/knowledge-base/seed")
async def seed_knowledge_base(user_id: str = DEFAULT_USER_ID):
    try:
        return knowledge_base_service.seed_sample_corpus(user_id=user_id)
    except KnowledgeBaseConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
