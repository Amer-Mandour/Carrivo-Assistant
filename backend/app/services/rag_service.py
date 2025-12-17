"""
خدمة RAG للبحث في الأسئلة الشائعة والمسارات
Hybrid Search Strategy:
1. RPC Vector Search (Database side - Primary)
2. Local Vector Search (Client side - Fallback if RPC fails)
3. Keyword Search (Last resort)
"""

from typing import List, Dict, Optional
import logging
import numpy as np
from ..database import get_supabase
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class RAGService:
    """خدمة البحث الذكي - Smart Search Service"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.embedding_service = EmbeddingService()
    
    async def search_faqs(self, query: str, language: str) -> List[Dict]:
        """
        بحث ذكي في الأسئلة الشائعة
        """
        try:
            # 1. Generate Embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # 2. Try RPC Vector Search (server-side)
            if query_embedding:
                try:
                    rpc_params = {
                        'query_embedding': query_embedding,
                        'match_count': 5,
                        'similarity_threshold': 0.5
                    }
                    results = self.supabase.rpc('match_faqs', rpc_params).execute()
                    if results.data:
                        logger.info(f"✅ FAQ Vector search (RPC) found {len(results.data)} results")
                        return results.data
                except Exception as rpc_error:
                    logger.warning(f"FAQ RPC search failed, trying fallback: {rpc_error}")

            # 3. Fallback: Client-Side Vector or Keyword Search
            logger.info("ℹ️ Running client-side fallback search for FAQs")
            
            # Fetch active FAQs
            result = self.supabase.table("faq").select("*").eq("is_active", True).execute()
            all_faqs = result.data if result.data else []
            
            if not all_faqs:
                return []
            
            # Determine target fields based on language
            # We search both but prioritize the requested language in scoring if needed
            # For simplicity, we search across the object
            
            # Use EmbeddingService's client-side search capability
            # It handles vector matching if embeddings exist, and keyword fallback if not
            results = await self.embedding_service.search_similar_roadmaps(
                query_text=query,
                roadmaps=all_faqs, # Reuse the generic search function
                limit=5,
                allow_fallback=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"FAQ search error: {e}")
            return []
    
    async def search_roadmaps(self, query: str, limit: int = 3) -> List[Dict]:
        """
        بحث ذكي في المسارات (Roadmaps)
        """
        try:
            # 1. Generate Embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # 2. Try RPC Search
            if query_embedding:
                try:
                    rpc_params = {
                        'query_embedding': query_embedding,
                        'match_count': limit,
                        'similarity_threshold': 0.5
                    }
                    results = self.supabase.rpc('match_roadmaps', rpc_params).execute()
                    if results.data:
                        logger.info(f"✅ Roadmap Vector search (RPC) found {len(results.data)} results")
                        return results.data
                except Exception as rpc_error:
                     logger.warning(f"Roadmap RPC search failed: {rpc_error}")

            # 3. Fallback: Client-Side
            # Fetch all published roadmaps
            # Note: For production with many rows, this is not efficient, but fine for fallback/small scale
            result = self.supabase.table("roadmaps").select("*").eq("is_published", True).execute()
            all_roadmaps = result.data if result.data else []

            results = await self.embedding_service.search_similar_roadmaps(
                query_text=query,
                roadmaps=all_roadmaps,
                limit=limit,
                allow_fallback=True
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Roadmap search error: {e}")
            return []