#!/usr/bin/env python3
"""
Local Embeddings Backfill - 100% Free, No API needed!
Uses sentence-transformers locally
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import get_supabase
from datetime import datetime
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Local Embeddings Backfill (100% Free!)")
    logger.info("=" * 70)
    
    # Load model (will download first time, ~400MB)
    logger.info("📥 Loading embedding model...")
    logger.info("   (First time will download ~400MB, please wait...)")
    
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions, fast & good
    logger.info("✅ Model loaded!\n")
    
    supabase = get_supabase()
    
    # Get roadmaps
    result = supabase.table("roadmaps").select("*").is_("embedding", "null").execute()
    roadmaps = result.data if result.data else []
    
    logger.info(f"📊 Found {len(roadmaps)} roadmaps to process\n")
    
    if not roadmaps:
        logger.info("✅ All roadmaps already have embeddings!")
        return
    
    success_count = 0
    
    # Process all at once (local is fast!)
    logger.info("🔄 Generating embeddings for all roadmaps...")
    
    # Prepare texts
    texts = []
    for rm in roadmaps:
        text = f"{rm['title']}. {rm.get('description', '')}. Category: {rm.get('category', '')}"
        texts.append(text)
    
    # Generate all embeddings at once
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    logger.info("\n💾 Saving to database...")
    
    # Update database
    for i, (roadmap, embedding) in enumerate(zip(roadmaps, embeddings), 1):
        try:
            # Convert numpy array to list
            embedding_list = embedding.tolist()
            
            # Pad or truncate to 1536 dimensions (to match DB schema)
            if len(embedding_list) < 1536:
                # Pad with zeros
                embedding_list = embedding_list + [0.0] * (1536 - len(embedding_list))
            else:
                # Truncate
                embedding_list = embedding_list[:1536]
            
            supabase.table("roadmaps").update({
                "embedding": embedding_list,
                "embedding_model": "all-MiniLM-L6-v2 (local)",
                "embedding_generated_at": datetime.now().isoformat()
            }).eq("id", roadmap["id"]).execute()
            
            logger.info(f"  [{i}/{len(roadmaps)}] ✅ {roadmap['title']}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  [{i}/{len(roadmaps)}] ❌ {roadmap['title']}: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"✅ Completed: {success_count}/{len(roadmaps)} ({success_count/len(roadmaps)*100:.0f}%)")
    logger.info("=" * 70)
    logger.info("\n🎉 Done! Your roadmaps now have AI embeddings!")
    logger.info("💡 Cost: $0.00 (100% free!)")

if __name__ == "__main__":
    asyncio.run(main())
