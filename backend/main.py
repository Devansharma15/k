from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, workflow, apps, files

app = FastAPI(title="AuraFlow Backend")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(workflow.router, prefix="/api", tags=["Workflow"])
app.include_router(apps.router, prefix="/api", tags=["Apps"])
app.include_router(files.router, prefix="/api", tags=["Files"])

@app.get("/")
async def root():
    return {"message": "AuraFlow API is running"}
