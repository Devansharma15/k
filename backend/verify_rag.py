import asyncio
from app.services.rag_service import rag_service
import os

async def verify_rag():
    print("--- AuraFlow RAG Verification ---")
    
    test_file = "data/auraflow_test.txt"
    if not os.path.exists(test_file):
        print(f"Error: {test_file} not found.")
        return

    print(f"Indexing {test_file}...")
    chunks = await rag_service.index_file(test_file)
    print(f"Successfully indexed {chunks} chunks.")

    query = "What is AuraFlow's mission?"
    print(f"\nQuerying: '{query}'")
    context = rag_service.retrieve_context(query)
    
    if context:
        print("\nRetrieved Context:")
        print(context)
        print("\nVERIFICATION SUCCESSFUL")
    else:
        print("\nERROR: No context retrieved.")

if __name__ == "__main__":
    asyncio.run(verify_rag())
