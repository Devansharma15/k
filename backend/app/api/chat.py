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

import os
import google.generativeai as genai

PROMPT_TEMPLATE = """You are a strict retrieval-based assistant.
Answer the question ONLY using the provided context.

----------------------------------------
RULES
----------------------------------------

- Use ONLY the context below.
- Do NOT use outside knowledge.
- If the answer is not found, say:
  "Not found in document"
- Be concise and structured.
- If possible, include supporting points from context.

----------------------------------------
CONTEXT
----------------------------------------
{context}

----------------------------------------
QUESTION
----------------------------------------
{question}

----------------------------------------
OUTPUT FORMAT
----------------------------------------

Answer:
<clear answer>

Supporting Evidence:
- <key point from context>
- <key point from context>"""

async def stream_rag_response(question: str, context: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        yield json.dumps({"token": "Error: GEMINI_API_KEY not found in environment. Raw context retrieved:\n\n" + context})
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = PROMPT_TEMPLATE.format(context=context if context else "[NO CONTEXT FOUND]", question=question)

    try:
        response = await model.generate_content_async(
            prompt,
            stream=True,
            generation_config={"temperature": 0.0}
        )
        async for chunk in response:
            if chunk.text:
                yield json.dumps({"token": chunk.text})
    except Exception as e:
        yield json.dumps({"token": f"\n\n[LLM Error: {str(e)}]"})

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        results = knowledge_base_service.query_dataset(
            dataset_id=request.dataset_id,
            query=request.message,
            top_k=5,
            user_id=DEFAULT_USER_ID
        )
        context_chunks = [res["text"] for res in results.get("results", [])]
        context_str = "\n\n---\n\n".join(context_chunks)
    except Exception as e:
        context_str = f"[Error retrieving context: {str(e)}]"
        
    return EventSourceResponse(stream_rag_response(request.message, context_str))
