from fastapi import APIRouter, UploadFile, File
import shutil
import os
from ..services.rag_service import rag_service

router = APIRouter()

UPLOAD_DIR = "backend/data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Trigger RAG Indexing
    try:
        chunks_indexed = await rag_service.index_file(file_path)
    except Exception as e:
        return {
            "filename": file.filename,
            "status": "Uploaded but Indexing Failed",
            "error": str(e)
        }
    
    return {
        "filename": file.filename,
        "status": "Uploaded & Indexed",
        "chunks": chunks_indexed,
        "path": file_path
    }
