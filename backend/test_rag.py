from app.services.rag_service import rag_service
print("RAG Service initialized")
context = rag_service.retrieve_context("test")
print(f"Context: {context}")
