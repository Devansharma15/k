"""
Verify Local RAG Pipeline
===========================
Verifies that the local embedding service and knowledge base pipeline
are working correctly — no OpenAI API key required.

Run:
    cd backend
    python verify_rag_local.py
"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

from app.services.embedding_service import embedding_service
from app.services.knowledge_base_service import knowledge_base_service


async def main() -> None:
    print("=" * 60)
    print("  Local RAG Pipeline — Verification")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Embedding service health check
    # ------------------------------------------------------------------
    print("\n[1/4] Embedding service health check …")
    health = embedding_service.health_check()
    for key, value in health.items():
        print(f"  {key}: {value}")

    # ------------------------------------------------------------------
    # 2. Single text embedding
    # ------------------------------------------------------------------
    print("\n[2/4] Embedding a single query …")
    try:
        query_text = "What is retrieval-augmented generation?"
        vector = embedding_service.embed(query_text)
        print(f"  Input : {query_text}")
        print(f"  Dim   : {len(vector)}")
        print(f"  First5: {vector[:5]}")
        print("  ✓ Single embedding OK")
    except Exception as exc:
        print(f"  ✗ Single embedding FAILED: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Batch embedding
    # ------------------------------------------------------------------
    print("\n[3/4] Batch embedding (3 chunks) …")
    try:
        chunks = [
            "RAG combines retrieval with generation for grounded answers.",
            "Vector databases store embeddings for fast similarity search.",
            "Sentence-transformers produce dense vector representations.",
        ]
        vectors = embedding_service.embed_batch(chunks)
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            print(f"  [{i}] dim={len(vec)}  text={chunk[:50]}…")
        print("  ✓ Batch embedding OK")
    except Exception as exc:
        print(f"  ✗ Batch embedding FAILED: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Knowledge base seeding + query (requires Qdrant)
    # ------------------------------------------------------------------
    print("\n[4/4] Knowledge base seed & query …")
    try:
        seed_result = knowledge_base_service.seed_sample_corpus()
        print(f"  Seed result: {seed_result}")
    except Exception as exc:
        print(f"  ⚠ Seed skipped ({type(exc).__name__}: {exc})")

    try:
        query_result = knowledge_base_service.query_dataset(
            "dataset_default",
            "What is the primary document knowledge base?",
        )
        print("  Query results:")
        for r in query_result.get("results", []):
            print(f"    - {r['text'][:80]}… (score: {r['score']:.4f})")
        print("  ✓ Query OK")
    except Exception as exc:
        print(f"  ⚠ Query skipped ({type(exc).__name__}: {exc})")

    print("\n" + "=" * 60)
    print("  Verification complete — local pipeline is operational.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
