-- ============================================================================
-- Migration: Add Vector Embeddings Support to Roadmaps
-- Purpose: Enable AI-powered semantic search using pgvector
-- Date: 2025-12-13
-- ============================================================================

-- Step 1: Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add embedding column to roadmaps table
-- Using 1536 dimensions (OpenAI text-embedding-3-small model)
ALTER TABLE roadmaps 
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- Step 3: Create index for fast vector similarity search
-- Using HNSW (Hierarchical Navigable Small World) for optimal performance
CREATE INDEX IF NOT EXISTS roadmaps_embedding_idx 
ON roadmaps 
USING hnsw (embedding vector_cosine_ops);

-- Step 4: Add metadata columns for tracking embedding generation
ALTER TABLE roadmaps 
ADD COLUMN IF NOT EXISTS embedding_model TEXT DEFAULT 'text-embedding-3-small',
ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMP WITH TIME ZONE;

-- Step 5: Create RPC function for vector similarity search
CREATE OR REPLACE FUNCTION match_roadmaps(
    query_embedding vector(1536),
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

-- Step 6: Add comment for documentation
COMMENT ON COLUMN roadmaps.embedding IS 'Vector embedding (768-dim) for semantic search using cosine similarity';
COMMENT ON FUNCTION match_roadmaps IS 'Performs vector similarity search on roadmaps using cosine distance';

-- Step 7: Grant necessary permissions
-- Allow the anon role to execute the RPC function
GRANT EXECUTE ON FUNCTION match_roadmaps TO anon;
GRANT EXECUTE ON FUNCTION match_roadmaps TO authenticated;
