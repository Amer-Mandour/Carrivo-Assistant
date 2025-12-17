#!/usr/bin/env python3
"""
Master Backfill Script:
1. Executes SQL Migration (Fix dimensions, add columns, create RPCs)
2. Generates & Updates Embeddings for Roadmaps
3. Generates & Updates Embeddings for FAQs
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import get_supabase
from app.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def run_sql_migration(supabase):
    """Run the SQL migration to fix dimensions and create functions"""
    logger.info("\n🛠️  Running SQL Migration...")
    logger.info("=" * 60)
    
    migration_file = Path("supabase/migrations/fix_embeddings_384_v2.sql")
    if not migration_file.exists():
        logger.error("❌ Migration file not found!")
        return False
        
    sql_content = migration_file.read_text(encoding='utf-8')
    
    # Supabase-py doesn't support executing raw SQL directly unless we use an RPC
    # OR we use the dashboard. 
    # BUT, we can try to use the `exec_sql` RPC if it exists (commonly added in these projects).
    # If not, we instruct the user.
    
    try:
        # Try to execute via 'exec_sql' RPC
        response = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
        logger.info("✅ Migration executed successfully (via exec_sql RPC)")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Could not auto-execute SQL: {e}")
        logger.warning("   (This is normal if 'exec_sql' RPC is not defined)")
        logger.info("\n📢  MANUAL ACTION REQUIRED:")
        logger.info("   Please copy the content of 'supabase/migrations/fix_embeddings_384_v2.sql'")
        logger.info("   and run it in the Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql\n")
        
        # We assume the user might have done this or we proceed hoping for the best?
        # If columns don't exist, the next steps will fail.
        # Let's verify if columns exist.
        try:
             supabase.table("roadmaps").select("embedding").limit(1).execute()
             supabase.table("faq").select("embedding").limit(1).execute()
             logger.info("✅ Columns 'embedding' seem to exist. Proceeding...")
             return True
        except Exception as check_err:
             logger.error(f"❌ Database checks failed. Columns missing? {check_err}")
             return False

async def backfill_roadmaps(supabase, embedding_service):
    """Backfill Roadmaps"""
    logger.info("\n🗺️  Backfilling Roadmaps...")
    logger.info("=" * 60)
    
    try:
        # Fetch all roadmaps
        result = supabase.table("roadmaps").select("*").execute()
        roadmaps = result.data if result.data else []
        
        if not roadmaps:
            logger.info("No roadmaps found to update.")
            return

        updates = 0
        for rm in roadmaps:
            # Combine text for embedding
            # requested strategy: Title + Description + Category
            text = f"{rm['title']} {rm.get('description', '')} {rm.get('category', '')}".strip()
            
            # Generate Embedding
            embedding = await embedding_service.generate_embedding(text)
            
            if embedding:
                try:
                    supabase.table("roadmaps").update({
                        "embedding": embedding,
                        "embedding_generated_at": datetime.now().isoformat()
                    }).eq("id", rm["id"]).execute()
                    # logger.info(f"  ✅ Updated: {rm['title']}")
                    print(".", end="", flush=True)
                    updates += 1
                except Exception as e:
                    logger.error(f"\n  ❌ Failed to update {rm['title']}: {e}")
            else:
                logger.warning(f"\n  ⚠️  Failed to generate embedding for {rm['title']}")
                
        logger.info(f"\n✅ Updated {updates}/{len(roadmaps)} roadmaps")
        
    except Exception as e:
        logger.error(f"Error backfilling roadmaps: {e}")

async def backfill_faqs(supabase, embedding_service):
    """Backfill FAQs"""
    logger.info("\n❓ Backfilling FAQs...")
    logger.info("=" * 60)
    
    try:
        # Fetch all FAQs
        result = supabase.table("faq").select("*").execute()
        faqs = result.data if result.data else []
        
        if not faqs:
            logger.info("No FAQs found to update.")
            return

        updates = 0
        for faq in faqs:
            # Combine text for embedding
            # requested strategy: All questions text
            q_ar = faq.get('question_ar', '')
            q_en = faq.get('question_en', '')
            text = f"{q_ar} {q_en}".strip()
            
            if not text:
                continue

            # Generate Embedding
            embedding = await embedding_service.generate_embedding(text)
            
            if embedding:
                try:
                    supabase.table("faq").update({
                        "embedding": embedding
                    }).eq("id", faq["id"]).execute()
                    # logger.info(f"  ✅ Updated FAQ: {q_ar[:30]}...")
                    print(".", end="", flush=True)
                    updates += 1
                except Exception as e:
                    logger.error(f"\n  ❌ Failed to update FAQ {faq['id']}: {e}")
            else:
                 logger.warning(f"\n  ⚠️  Failed to generate embedding for FAQ {faq['id']}")
                 
        logger.info(f"\n✅ Updated {updates}/{len(faqs)} FAQs")
        
    except Exception as e:
        logger.error(f"Error backfilling FAQs: {e}")

async def main():
    logger.info("🚀 Starting Master Backfill...")
    
    supabase = get_supabase()
    embedding_service = EmbeddingService()
    
    # Ensure model is loaded
    if not embedding_service.is_available():
        logger.error("❌ Embedding service failed to initialize. Aborting.")
        return

    # 1. Run Migration (or verify)
    migration_ok = await run_sql_migration(supabase)
    
    if not migration_ok:
        logger.info("⚠️  Proceeding with backfill anyway (hoping tables are ready)...")

    # 2. Backfill Roadmaps
    await backfill_roadmaps(supabase, embedding_service)
    
    # 3. Backfill FAQs
    await backfill_faqs(supabase, embedding_service)
    
    logger.info("\n🎉 Master Backfill Completed!")

if __name__ == "__main__":
    asyncio.run(main())
