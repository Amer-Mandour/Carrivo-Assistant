
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import get_supabase
from app.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def force_fix_faqs():
    supabase = get_supabase()
    embedding_service = EmbeddingService()
    
    print("\n[INFO] Fetching ALL FAQs...")
    res = supabase.table("faq").select("*").execute()
    faqs = res.data or []
    print(f"   Found {len(faqs)} FAQs.")
    
    if not faqs:
        print("   No FAQs found!")
        return

    print("\n[ACTION] Generating and Updating Embeddings for ALL FAQs...")
    
    for faq in faqs:
        # Combine text: Question (AR) + Question (EN) + Answer (AR) + Answer (EN)
        # to ensure rich context
        text_parts = [
            faq.get('question_ar', ''),
            faq.get('question_en', ''),
            faq.get('answer_ar', ''),
            faq.get('answer_en', '')
        ]
        text = " ".join([t for t in text_parts if t]).strip()
        
        print(f"   - Processing ID: {faq['id']}")
        # print(f"     Text preview: {text[:50]}...")
        
        emb = await embedding_service.generate_embedding(text)
        
        if emb:
            try:
                # Force update
                supabase.table("faq").update({
                    "embedding": emb, 
                    "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2" # if column exists
                }).eq("id", faq['id']).execute()
                print("     ✅ Updated successfully.")
            except Exception as e:
                # Try without embedding_model column if it fails
                try:
                    supabase.table("faq").update({
                        "embedding": emb
                    }).eq("id", faq['id']).execute()
                    print("     ✅ Updated successfully (embedding only).")
                except Exception as e2:
                    print(f"     ❌ Update failed: {e2}")
        else:
            print("     ❌ Failed to generate embedding.")

    print("\n[VERIFICATION] Reading back from DB...")
    res_verify = supabase.table("faq").select("id, question_ar, embedding").execute()
    for row in res_verify.data:
        has_emb = "✅ Present" if row.get('embedding') else "❌ NULL"
        print(f"   - {row.get('question_ar')[:30]}... : {has_emb}")

if __name__ == "__main__":
    asyncio.run(force_fix_faqs())
