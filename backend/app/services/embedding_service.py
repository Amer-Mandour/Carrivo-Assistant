"""
خدمة توليد الـ Embeddings - Local Implementation
Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
Native 384 dimensions - NO OpenAI dependencies
"""

from typing import List, Optional, Dict
import logging
import numpy as np
from ..database import get_supabase

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Local Embedding Service using SentenceTransformer
    Model: paraphrase-multilingual-MiniLM-L12-v2
    Dimensions: 384
    """
    
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.initialize_model()
        return cls._instance

    def initialize_model(self):
        """Initialize the model singleton if not already loaded"""
        if self._model is not None:
            return

        # 🚀 PRODUCTION OPTIMIZATION: Skip loading heavy model on free tier servers
        # Import settings here to avoid circular imports
        from ..config import settings
        if settings.app_env.lower() == "production":
            logger.info("🚀 Production Environment: Skipping local embedding model to save RAM (512MB limit).")
            logger.info("⚡ Using Fuzzy Search fallback instead.")
            self._available = False
            return

        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2" 
        self.embedding_dim = 384
        self._available = False
        
        try:
            # Lazy Import to save memory on startup
            from sentence_transformers import SentenceTransformer
            logger.info("📥 Loading embedding model (this may take a moment)...")
            self._model = SentenceTransformer(self.model_name)
            self._available = True
            logger.info(f"✅ Embedding service initialized (Model: {self.model_name}, {self.embedding_dim}-dim)")
        except Exception as e:
            logger.error(f"❌ Failed to init local model: {e}")
            self._available = False

    def is_available(self) -> bool:
        return self._available
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate a single embedding vector (384 dimensions)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
        
        if not self._available:
            logger.error("Embedding model is not available")
            return None
        
        try:
            # Generate embedding via local model
            # encode returns numpy array, convert to list
            embedding = self._model.encode(text.strip()).tolist()
            
            if len(embedding) != self.embedding_dim:
                logger.error(f"Dimension mismatch! Expected {self.embedding_dim}, got {len(embedding)}")
                return None
                
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts in batch
        """
        if not texts:
            return None
        
        # Filter empty texts but keep tracking indices if needed (handled by list comp below)
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return None
        
        if not self._available:
             return None
        
        try:
            embeddings_array = self._model.encode(valid_texts)
            embeddings = embeddings_array.tolist()
            
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts using the model
        """
        try:
            emb1 = self._model.encode(text1)
            emb2 = self._model.encode(text2)
            
            return self._calculate_cosine_similarity(emb1, emb2)
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0

    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    async def search_similar_roadmaps(
        self, 
        query_text: str, 
        roadmaps: List[Dict],
        limit: int = 5,
        allow_fallback: bool = True
    ) -> List[Dict]:
        """
        Client-side semantic search (Vector -> Keyword Fallback)
        """
        if not roadmaps:
            return []
            
        try:
            # 1. Try Vector Search
            if self._available:
                query_embedding = await self.generate_embedding(query_text)
                
                if query_embedding:
                    query_vec = np.array(query_embedding)
                    scored_roadmaps = []
                    
                    for roadmap in roadmaps:
                        roadmap_emb = roadmap.get('embedding')
                        
                        if not roadmap_emb:
                            continue
                            
                        doc_vec = np.array(roadmap_emb)
                        
                        if query_vec.shape != doc_vec.shape:
                            # Skip mismatch instead of crashing
                            continue
                        
                        score = self._calculate_cosine_similarity(query_vec, doc_vec)
                        
                        scored_roadmaps.append({
                            **roadmap,
                            'similarity': score, # Standardize key
                            'similarity_score': score
                        })
                    
                    if scored_roadmaps:
                        scored_roadmaps.sort(key=lambda x: x['similarity'], reverse=True)
                        return scored_roadmaps[:limit]
            
            # 2. Fallback
            if allow_fallback:
                return self._keyword_search_fallback(query_text, roadmaps, limit)
            
            return []
            
        except Exception as e:
            logger.error(f"Error in client-side search: {e}")
            if allow_fallback:
                return self._keyword_search_fallback(query_text, roadmaps, limit)
            return []

    def _keyword_search_fallback(
        self, 
        query_text: str, 
        items: List[Dict],
        limit: int = 5
    ) -> List[Dict]:
        """
        Simple keyword overlap fallback
        """
        try:
            scored_items = []
            query_parts = set(query_text.lower().split())
            
            for item in items:
                # Construct searchable text from available common fields
                # Supports both Roadmap and FAQ structures
                text_parts = [
                    item.get('title', ''),
                    item.get('description', ''),
                    item.get('category', ''),
                    item.get('question_ar', ''),
                    item.get('question_en', ''),
                    item.get('answer_ar', ''),
                    item.get('answer_en', '')
                ]
                item_text = " ".join([str(t) for t in text_parts if t]).lower()
                
                item_words = set(item_text.split())
                if not item_words or not query_parts:
                    score = 0.0
                else:
                    intersection = query_parts.intersection(item_words)
                    score = len(intersection) / len(query_parts)
                
                if score > 0:
                    scored_items.append({
                        **item,
                        'similarity': score,
                        'similarity_score': score
                    })
            
            scored_items.sort(key=lambda x: x['similarity'], reverse=True)
            return scored_items[:limit]
            
        except Exception as e:
            logger.error(f"Error in keyword fallback: {e}")
            return []