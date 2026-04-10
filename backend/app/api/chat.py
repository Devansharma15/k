from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from ..services.knowledge_base_service import knowledge_base_service, DEFAULT_USER_ID

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-4o"
    dataset_id: str = "dataset_default"

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
    try:
        results = knowledge_base_service.query_dataset(
            dataset_id=request.dataset_id,
            query=request.message,
            top_k=3,
            user_id=DEFAULT_USER_ID
        )
        context_chunks = [res["text"] for res in results.get("results", [])]
        context_str = "\n\n---\n\n".join(context_chunks)
    except Exception as e:
        context_str = f"[Error retrieving context: {str(e)}]"
        
    return EventSourceResponse(mock_stream_response(request.message, context_str))
