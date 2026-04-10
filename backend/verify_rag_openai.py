import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app.services.knowledge_base_service import knowledge_base_service

async def main():
    print("--- Verifying OpenAI RAG setup ---")
    
    # Check OpenAI Key
    import openai
    if not os.getenv("OPENAI_API_KEY"):
        print("Need OPENAI_API_KEY to verify")
        sys.exit(1)
        
    print("Seeding sample corpus...")
    try:
        res = knowledge_base_service.seed_sample_corpus()
        print(f"Seed Success: {res}")
    except Exception as e:
        print(f"Seed Failed: {e}")
        return
        
    print("\nQuerying knowledge base...")
    try:
        res = knowledge_base_service.query_dataset("dataset_default", "What is the primary document knowledge base?")
        print(f"Query Result:")
        for r in res.get("results", []):
            print(f"- {r['text'][:100]}... (Score: {r['score']})")
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
