
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import get_supabase
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def verify_and_fix():
    supabase = get_supabase()
    embedding_service = EmbeddingService()
    rag_service = RAGService()
    
    print("\n[INFO] 1. Inspecting FAQ Embeddings...")
    res = supabase.table("faq").select("id, question_ar, embedding").execute()
    faqs = res.data or []
    
    null_count = len([f for f in faqs if not f.get('embedding')])
    print(f"   Found {len(faqs)} FAQs. {null_count} have NULL embeddings.")
    
    if null_count > 0:
        print("\n[ACTION] 2. Attempting to Backfill FAQs...")
        for faq in faqs:
            if faq.get('embedding'):
                continue
                
            text = f"{faq.get('question_ar', '')} {faq.get('question_en', '')}".strip()
            print(f"   Generating embedding for: {text[:30]}...")
            
            emb = await embedding_service.generate_embedding(text)
            if emb:
                try:
                    # Update
                    print(f"   Saving to DB ID: {faq['id']}...")
                    supabase.table("faq").update({"embedding": emb}).eq("id", faq['id']).execute()
                    print("   - Saved.")
                except Exception as e:
                    print(f"   - Failed to save: {e}")
                    # Try to force schema cache reload by calling a unknown endpoint or just log
                    if "schema cache" in str(e):
                        print("   - Hint: Go to Supabase Dashboard -> Settings -> API -> 'Reload Schema Cache'")
    
    print("\n[TEST] 3. Testing Semantic Search (RPC)...")
    # Test query that matches one of the questions
    test_query = "ازاي ابدأ برمجة" # Close to "ازاي ابدأ اتعلم برمجة؟"
    print(f"   Query: '{test_query}'")
    
    results = await rag_service.search_faqs(test_query, "ar")
    
    if results:
        print(f"   [SUCCESS] Search Success! Found {len(results)} results.")
        for r in results:
            sim = r.get('similarity', 0)
            print(f"      - {r.get('question_ar')} (Score: {sim:.4f})")
    else:
        print("   [FAILURE] Search returned NO results.")

if __name__ == "__main__":
    asyncio.run(verify_and_fix())
