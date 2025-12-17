#!/usr/bin/env python3
"""
Re-generate embeddings with multilingual model (better for Arabic!)
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
    logger.info("🚀 Re-generating embeddings with Multilingual Model")
    logger.info("=" * 70)
    logger.info("Model: paraphrase-multilingual-MiniLM-L12-v2")
    logger.info("Better for: Arabic, English, and 50+ languages!")
    logger.info("=" * 70)
    
    # Load multilingual model
    logger.info("\n📥 Loading multilingual model...")
    logger.info("   (First time will download ~400MB, please wait...)")
    
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    logger.info("✅ Model loaded!\n")
    
    supabase = get_supabase()
    
    # Get ALL roadmaps (force re-generate)
    result = supabase.table("roadmaps").select("*").execute()
    roadmaps = result.data if result.data else []
    
    logger.info(f"📊 Found {len(roadmaps)} roadmaps to re-process\n")
    
    if not roadmaps:
        logger.info("❌ No roadmaps found!")
        return
    
    success_count = 0
    
    # Process all at once
    logger.info("🔄 Generating embeddings for all roadmaps...")
    
    # Prepare texts
    texts = []
    for rm in roadmaps:
        text = rm['title'].strip()
        texts.append(text)
    
    # Generate all embeddings at once
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    logger.info("\n💾 Saving to database...")
    
    # Update database
    for i, (roadmap, embedding) in enumerate(zip(roadmaps, embeddings), 1):
        try:
            # Convert numpy array to list (native 384 dimensions)
            embedding_list = embedding.tolist()
            
            supabase.table("roadmaps").update({
                "embedding": embedding_list,
                "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
                "embedding_generated_at": datetime.now().isoformat()
            }).eq("id", roadmap["id"]).execute()
            
            logger.info(f"  [{i}/{len(roadmaps)}] ✅ {roadmap['title']}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  [{i}/{len(roadmaps)}] ❌ {roadmap['title']}: {e}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"✅ Completed: {success_count}/{len(roadmaps)} ({success_count/len(roadmaps)*100:.0f}%)")
    logger.info("=" * 70)
    logger.info("\n🎉 Done! Embeddings updated with multilingual model!")
    logger.info("💡 Better accuracy for Arabic queries!")

if __name__ == "__main__":
    asyncio.run(main())
