-- ============================================================================
-- Migration: Update to Multilingual Embeddings (384 dimensions)
-- Purpose: Switch from OpenAI embeddings (1536-dim) to local multilingual model (384-dim)
-- Model: paraphrase-multilingual-MiniLM-L12-v2 (Better for Arabic!)
-- Date: 2025-12-13
-- ============================================================================

-- Step 1: Drop old RPC function
DROP FUNCTION IF EXISTS match_roadmaps(vector, int, float);

-- Step 2: Drop old index
DROP INDEX IF EXISTS roadmaps_embedding_idx;

-- Step 3: Drop old embedding column
ALTER TABLE roadmaps DROP COLUMN IF EXISTS embedding;

-- Step 4: Add new embedding column with 384 dimensions
ALTER TABLE roadmaps 
ADD COLUMN embedding vector(384);

-- Step 5: Create new index for 384-dim vectors
CREATE INDEX roadmaps_embedding_idx 
ON roadmaps 
USING hnsw (embedding vector_cosine_ops);

-- Step 6: Update embedding_model default
ALTER TABLE roadmaps 
ALTER COLUMN embedding_model SET DEFAULT 'paraphrase-multilingual-MiniLM-L12-v2';

-- Step 7: Create new RPC function for 384-dim vectors
CREATE OR REPLACE FUNCTION match_roadmaps(
    query_embedding vector(384),
    match_count int DEFAULT 5,
    similarity_threshold float DEFAULT 0.5
)
RETURNS TABLE (
    id uuid,
    title text,
    slug text,
    description text,
    url text,
    category text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.title,
        r.slug,
        r.description,
        r.url,
        r.category,
        1 - (r.embedding <=> query_embedding) AS similarity
    FROM roadmaps r
    WHERE r.embedding IS NOT NULL
        AND 1 - (r.embedding <=> query_embedding) > similarity_threshold
    ORDER BY r.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Step 8: Update comments
COMMENT ON COLUMN roadmaps.embedding IS 'Vector embedding (384-dim) using paraphrase-multilingual-MiniLM-L12-v2 for better Arabic support';
COMMENT ON FUNCTION match_roadmaps IS 'Performs vector similarity search on roadmaps using cosine distance (384-dim multilingual embeddings)';

-- Step 9: Grant permissions
GRANT EXECUTE ON FUNCTION match_roadmaps TO anon;
GRANT EXECUTE ON FUNCTION match_roadmaps TO authenticated;

-- ============================================================================
-- Migration Complete!
-- Next Steps:
-- 1. Run this migration in Supabase SQL Editor
-- 2. Run: python backfill_multilingual.py to generate new embeddings
-- ============================================================================
