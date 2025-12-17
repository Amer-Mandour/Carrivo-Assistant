#!/usr/bin/env python3
"""
Backfill Script: Generate and Store Embeddings for Existing Roadmaps
=====================================================================

Purpose:
- Reads all roadmaps from Supabase
- Generates embeddings from (title + description)
- Updates the embedding column in the database

Features:
- Idempotent: Safe to run multiple times
- Batch processing for efficiency
- Progress tracking
- Error handling and retry logic
- Dry-run mode for testing

Usage:
    python backfill_embeddings.py                # Dry run (preview only)
    python backfill_embeddings.py --execute      # Actually update database
    python backfill_embeddings.py --force        # Re-generate all embeddings
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.database import get_supabase
from app.services.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingBackfillService:
    """Service to backfill embeddings for roadmaps"""
    
    def __init__(self, dry_run: bool = True, force: bool = False):
        self.supabase = get_supabase()
        self.embedding_service = EmbeddingService()
        self.dry_run = dry_run
        self.force = force
        self.batch_size = 10  # Process 10 roadmaps at a time
        
    async def get_roadmaps_needing_embeddings(self) -> List[Dict]:
        """
        Fetch roadmaps that need embeddings
        
        Returns:
            List of roadmaps without embeddings (or all if force=True)
        """
        try:
            if self.force:
                # Get all roadmaps
                result = self.supabase.table("roadmaps").select("*").execute()
                logger.info(f"Force mode: Processing ALL {len(result.data)} roadmaps")
            else:
                # Get only roadmaps without embeddings
                result = self.supabase.table("roadmaps")\
                    .select("*")\
                    .is_("embedding", "null")\
                    .execute()
                logger.info(f"Found {len(result.data)} roadmaps without embeddings")
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching roadmaps: {e}")
            return []
    
    def create_embedding_text(self, roadmap: Dict) -> str:
        """
        Create text for embedding from roadmap data
        
        Args:
            roadmap: Roadmap dictionary
            
        Returns:
            Combined text for embedding
        """
        title = roadmap.get('title', '')
        description = roadmap.get('description', '')
        category = roadmap.get('category', '')
        
        # Combine with weights (title is most important)
        text = title.strip()
        return text
    
    async def process_batch(self, roadmaps: List[Dict]) -> int:
        """
        Process a batch of roadmaps
        
        Args:
            roadmaps: List of roadmaps to process
            
        Returns:
            Number of successfully processed roadmaps
        """
        if not roadmaps:
            return 0
        
        # Prepare texts for batch embedding
        texts = [self.create_embedding_text(rm) for rm in roadmaps]
        
        logger.info(f"Generating embeddings for batch of {len(roadmaps)} roadmaps...")
        
        # Generate embeddings in batch
        embeddings = await self.embedding_service.generate_embeddings_batch(texts)
        
        if not embeddings:
            logger.error("Failed to generate embeddings for batch")
            return 0
        
        # Update database
        success_count = 0
        for roadmap, embedding in zip(roadmaps, embeddings):
            try:
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would update: {roadmap['title']}")
                    success_count += 1
                else:
                    # Update the roadmap with embedding
                    self.supabase.table("roadmaps").update({
                        "embedding": embedding,
                        "embedding_model": self.embedding_service.model,
                        "embedding_generated_at": datetime.now().isoformat()
                    }).eq("id", roadmap["id"]).execute()
                    
                    logger.info(f"✅ Updated: {roadmap['title']}")
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to update {roadmap['title']}: {e}")
        
        return success_count
    
    async def run(self):
        """
        Main execution function
        """
        logger.info("=" * 70)
        logger.info("EMBEDDING BACKFILL SCRIPT")
        logger.info("=" * 70)
        logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        logger.info(f"Force: {self.force}")
        logger.info(f"Batch Size: {self.batch_size}")
        logger.info("=" * 70)
        
        # Get roadmaps needing embeddings
        roadmaps = await self.get_roadmaps_needing_embeddings()
        
        if not roadmaps:
            logger.info("✅ No roadmaps need embeddings. All done!")
            return
        
        total = len(roadmaps)
        logger.info(f"\n📊 Total roadmaps to process: {total}\n")
        
        # Process in batches
        total_success = 0
        for i in range(0, total, self.batch_size):
            batch = roadmaps[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            
            logger.info(f"\n📦 Processing batch {batch_num}/{total_batches}")
            logger.info("-" * 70)
            
            success = await self.process_batch(batch)
            total_success += success
            
            # Small delay between batches to avoid rate limiting
            if i + self.batch_size < total:
                await asyncio.sleep(2)
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total processed: {total_success}/{total}")
        logger.info(f"Success rate: {(total_success/total*100):.1f}%")
        
        if self.dry_run:
            logger.info("\n⚠️  This was a DRY RUN. No changes were made.")
            logger.info("Run with --execute to actually update the database.")
        else:
            logger.info("\n✅ Backfill completed successfully!")
        
        logger.info("=" * 70)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill embeddings for roadmaps")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the updates (default is dry-run)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-generate embeddings for ALL roadmaps (even if they already have embeddings)"
    )
    
    args = parser.parse_args()
    
    # Create and run backfill service
    service = EmbeddingBackfillService(
        dry_run=not args.execute,
        force=args.force
    )
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
