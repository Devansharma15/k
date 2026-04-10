from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from app.api import apps, chat, integrations, knowledge_base, overview, workflow, workflow_platform

print("Starting AuraFlow Backend...")
app = FastAPI(title="AuraFlow Backend")
print("FastAPI app created.")

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
app.include_router(integrations.router, prefix="/api", tags=["Integrations"])
app.include_router(knowledge_base.router, prefix="/api", tags=["Knowledge Base"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(workflow.router, prefix="/api", tags=["Workflow"])
app.include_router(workflow_platform.router, prefix="/api", tags=["Workflow Platform"])
app.include_router(apps.router, prefix="/api", tags=["Apps"])

@app.get("/")
async def root():
    return {"message": "AuraFlow API is running"}
