from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import apps, chat, files, overview, workflow

app = FastAPI(title="AuraFlow Backend")

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(overview.router, prefix="/api", tags=["Overview"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(workflow.router, prefix="/api", tags=["Workflow"])
app.include_router(apps.router, prefix="/api", tags=["Apps"])
app.include_router(files.router, prefix="/api", tags=["Files"])

@app.get("/")
async def root():
    return {"message": "AuraFlow API is running"}
