"""
خدمة Roadmaps - للبحث والحصول على المسارات التعليمية مع دعم Fuzzy Matching
"""

from typing import List, Dict, Optional
import logging
from difflib import SequenceMatcher
from ..database import get_supabase

logger = logging.getLogger(__name__)

class RoadmapService:
    """خدمة للتعامل مع Roadmaps مع بحث ذكي"""
    
    # خريطة الكلمات المشابهة (Synonyms)
    SYNONYMS = {
        # AI/ML - توسيع كبير
        "ذكاء": ["ai", "artificial intelligence", "machine learning", "data scientist", "mlops"],
        "اصطناعي": ["ai", "artificial intelligence", "machine learning", "data scientist"],
        "ذكاء اصطناعي": ["ai", "artificial intelligence", "machine learning", "data scientist", "mlops"],
        "ai": ["artificial intelligence", "machine learning", "data scientist", "mlops", "data science"],
        "artificial intelligence": ["ai", "machine learning", "data scientist", "mlops"],
        "machine learning": ["ai", "data scientist", "mlops", "ml"],
        "ml": ["machine learning", "ai", "mlops", "data scientist"],
        "data science": ["ai", "data scientist", "machine learning"],
        "بيانات": ["data", "data scientist", "ai"],
        
        # Web Development
        "ويب": ["web", "frontend", "backend", "full stack"],
        "web": ["frontend", "backend", "full stack"],
        "فرونت": ["frontend", "react", "javascript"],
        "فرونت اند": ["frontend", "react", "javascript", "web"],
        "فرونت إند": ["frontend", "react", "javascript", "web"],
        "الفرونت": ["frontend", "react", "javascript"],
        "frontend": ["react", "javascript", "web"],
        "باك": ["backend", "node", "python", "java"],
        "باك اند": ["backend", "node", "python", "java", "web"],
        "باك إند": ["backend", "node", "python", "java", "web"],
        "الباك": ["backend", "node", "python", "java"],
        "backend": ["node", "python", "java", "web"],
        "full stack": ["frontend", "backend", "web"],
        "فول ستاك": ["full stack", "frontend", "backend"],
        
        # Mobile
        "موبايل": ["mobile", "android", "flutter", "react native"],
        "mobile": ["android", "flutter", "react native"],
        "اندرويد": ["android", "mobile"],
        "android": ["mobile"],
        "flutter": ["mobile"],
        
        # DevOps
        "ديف اوبس": ["devops", "docker", "kubernetes"],
        "devops": ["docker", "kubernetes"],
        "docker": ["devops", "kubernetes"],
        "kubernetes": ["devops", "docker"],
        
        # Security
        "امن": ["security", "cyber security", "cyber"],
        "امان": ["security", "cyber security"],
        "security": ["cyber security", "cyber"],
        "cyber": ["security", "cyber security"],
        
        # Database
        "قواعد بيانات": ["database", "sql", "mongodb", "postgresql"],
        "database": ["sql", "mongodb", "postgresql"],
        "sql": ["database", "postgresql"],
        "mongodb": ["database"],
        "postgresql": ["database", "sql"],
        
        # Design
        "تصميم": ["design", "ux"],
        "design": ["ux"],
        "ux": ["design"],
        
        # Blockchain
        "بلوكتشين": ["blockchain"],
        "blockchain": ["web3"],
        "web3": ["blockchain"],
        
        # Programming Languages
        "python": ["backend", "ai", "data scientist"],
        "java": ["backend"],
        "javascript": ["frontend", "backend", "node"],
        "react": ["frontend"],
        "node": ["backend"],
        "go": ["backend"],
        "golang": ["go", "backend"],
    }
    
    def __init__(self):
        self.supabase = get_supabase()
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """حساب نسبة التشابه بين نصين"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _expand_query(self, query: str) -> List[str]:
        """توسيع الاستعلام بإضافة الكلمات المشابهة"""
        query_lower = query.lower()
        expanded = [query_lower]
        
        # البحث في الـ Synonyms
        for key, synonyms in self.SYNONYMS.items():
            if key in query_lower:
                expanded.extend(synonyms)
            for synonym in synonyms:
                if synonym in query_lower:
                    expanded.append(key)
                    expanded.extend(synonyms)
        
        # إزالة التكرار
        return list(set(expanded))
    
    async def search_roadmaps(self, query: str, limit: int = 5, use_embeddings: bool = True) -> List[Dict]:
        """
        HYBRID SEARCH: Vector Embeddings (primary) + Fuzzy Matching (fallback)
        
        Search Flow:
        1. Try vector search using embeddings (if available)
        2. If vector search fails or returns poor results, fallback to fuzzy matching
        3. Return best results from either method
        
        Args:
            query: Search query text
            limit: Number of results to return
            use_embeddings: Whether to attempt vector search (default: True)
        
        Returns:
            List of roadmaps ranked by relevance
        """
        try:
            # ============================================================
            # PHASE 1: Vector Search (Primary Method)
            # ============================================================
            if use_embeddings:
                vector_results = await self._vector_search(query, limit)
                
                # If vector search succeeded with good results, use it
                if vector_results and len(vector_results) > 0:
                    # Check quality of top result
                    top_similarity = vector_results[0].get('similarity', 0)
                    
                    if top_similarity > 0.6:  # High confidence threshold
                        logger.info(f"✅ Vector search succeeded (top similarity: {top_similarity:.2f})")
                        return vector_results
                    else:
                        logger.info(f"⚠️ Vector search returned low-confidence results (top: {top_similarity:.2f})")
            
            # ============================================================
            # PHASE 2: Fuzzy Matching Fallback
            # ============================================================
            logger.info("🔄 Falling back to fuzzy matching...")
            fuzzy_results = await self._fuzzy_search(query, limit)
            
            return fuzzy_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Last resort: try fuzzy matching
            return await self._fuzzy_search(query, limit)
    
    async def _vector_search(self, query: str, limit: int) -> List[Dict]:
        """
        Vector similarity search using Supabase RPC
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of roadmaps with similarity scores
        """
        try:
            # Import embedding service
            from .embedding_service import EmbeddingService
            embedding_service = EmbeddingService()
            
            # Check if embedding service is available
            if not embedding_service.is_available():
                logger.warning("Embedding service not available, skipping vector search")
                return []
            
            # Generate query embedding
            logger.info(f"Generating embedding for query: '{query[:50]}...'")
            query_embedding = await embedding_service.generate_embedding(query)
            
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []
            
            # Call Supabase RPC function for vector search
            result = self.supabase.rpc(
                'match_roadmaps',
                {
                    'query_embedding': query_embedding,
                    'match_count': limit,
                    'similarity_threshold': 0.5  # Minimum similarity
                }
            ).execute()
            
            if result.data:
                logger.info(f"Vector search found {len(result.data)} results")
                return result.data
            else:
                logger.info("Vector search returned no results")
                return []
                
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def _fuzzy_search(self, query: str, limit: int) -> List[Dict]:
        """
        FALLBACK: Fuzzy matching search (original implementation)
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of roadmaps with similarity scores
        """
        try:
            # Get all roadmaps from database
            result = self.supabase.table("roadmaps").select("*").execute()
            all_roadmaps = result.data if result.data else []
            
            if not all_roadmaps:
                return []
            
            # -----------------------------------------------------------------
            # IMPROVEMENT: Try Client-Side Vector Search if embeddings exist
            # -----------------------------------------------------------------
            try:
                from .embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                
                # Check if we have embeddings in the fetched data
                if any(r.get('embedding') for r in all_roadmaps) and embedding_service.is_available():
                    logger.info("ℹ️ Attempting client-side vector search on fetched roadmaps...")
                    # search_similar_roadmaps now implements proper vector cosine similarity
                    vector_results = await embedding_service.search_similar_roadmaps(query, all_roadmaps, limit, allow_fallback=False)
                    
                    if vector_results:
                        logger.info(f"✅ Client-side vector search found {len(vector_results)} results")
                        return vector_results
            except Exception as vec_error:
                logger.warning(f"Client-side vector search failed, continuing to fuzzy match: {vec_error}")
            
            # -----------------------------------------------------------------
            # TEXT MATCHING (Original Logic)
            # -----------------------------------------------------------------
            
            # Expand query with synonyms
            expanded_queries = self._expand_query(query)
            
            scored_roadmaps = []
            for roadmap in all_roadmaps:
                max_score = 0
                
                # Clean text for matching
                title_clean = roadmap['title'].lower().replace('&', 'and').replace('-', ' ')
                desc_clean = roadmap.get('description', '').lower().replace('&', 'and').replace('-', ' ')
                cat_clean = roadmap.get('category', '').lower().replace('/', ' ').replace('-', ' ')
                
                searchable_text = f"{title_clean} {desc_clean} {cat_clean}"
                
                # Calculate maximum similarity score
                for exp_query in expanded_queries:
                    exp_query_clean = exp_query.replace('&', 'and').replace('-', ' ')
                    
                    # Direct match (highest score)
                    if exp_query_clean in searchable_text:
                        max_score = max(max_score, 1.0)
                        break
                    
                    # Partial match using SequenceMatcher
                    title_score = self._calculate_similarity(exp_query_clean, title_clean)
                    desc_score = self._calculate_similarity(exp_query_clean, desc_clean)
                    cat_score = self._calculate_similarity(exp_query_clean, cat_clean)
                    max_score = max(max_score, title_score, desc_score, cat_score)
                
                if max_score > 0.15:  # Minimum threshold
                    scored_roadmaps.append({
                        **roadmap,
                        'similarity_score': max_score,
                        'similarity': max_score  # Alias for consistency with vector search
                    })
            
            # Sort by similarity
            scored_roadmaps.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Fuzzy search found {len(scored_roadmaps)} results")
            return scored_roadmaps[:limit]
            
        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return []
    
    async def get_roadmap_by_slug(self, slug: str) -> Optional[Dict]:
        """
        الحصول على Roadmap محدد بواسطة slug
        """
        try:
            result = self.supabase.table("roadmaps").select("*").eq("slug", slug).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting roadmap: {e}")
            return None
    
    async def get_all_roadmaps(self, category: Optional[str] = None) -> List[Dict]:
        """
        الحصول على جميع الـ Roadmaps أو حسب الفئة
        """
        try:
            query = self.supabase.table("roadmaps").select("*")
            
            if category:
                query = query.eq("category", category)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting all roadmaps: {e}")
            return []
    
    async def get_categories(self) -> List[str]:
        """
        الحصول على جميع الفئات المتاحة
        """
        try:
            result = self.supabase.table("roadmaps").select("category").execute()
            categories = list(set([r['category'] for r in result.data if r.get('category')]))
            return sorted(categories)
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
