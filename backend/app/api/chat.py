from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from ..services.rag_service import rag_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o"

async def mock_stream_response(message: str, context: str):
    """Mocks a streaming response using retrieved context."""
    if context:
        prompt = f"Context: {context}\n\nQuestion: {message}\n\nAnswer based ON THE CONTEXT ONLY:"
    else:
        prompt = message
        
    responses = [
        "AuraFlow ", "RAG ", "Engine ", "Active: \n\n",
        f"Retrieving context for your query... \n\n",
        f"Based on the knowledge base: \n\n",
        "Found relevant matches. " if context else "No relevant documents found. Using general knowledge. ",
        "\n\nGenerating response... \n\n",
    ]
    
    # Mocking a response that "refers" to context if available
    if context:
        responses.append("The documents mention that ")
        responses.append(context[:100].replace('\n', ' '))
        responses.append("... [Source: Document Index]")
    else:
        responses.append(f"Processing your request: '{message}'")
        
    for word in responses:
        yield json.dumps({"token": word})
        await asyncio.sleep(0.05)

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Perform Similarity Search
    context = rag_service.retrieve_context(request.message)
    return EventSourceResponse(mock_stream_response(request.message, context))
