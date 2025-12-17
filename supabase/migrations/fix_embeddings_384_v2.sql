-- Migration: Fix Embeddings to 384 dimensions and add FAQ support
-- ================================================================

-- 1. Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Update ROADMAPS table
-- ------------------------
-- First, drop the index if it exists to avoid conflicts
DROP INDEX IF EXISTS roadmaps_embedding_idx;

-- We need to change the column type. 
-- If there is data with wrong dimensions (1536), we need to clear it or cast it.
-- Since we are backfilling anyway, it's safer to clear invalid data or restart.
-- We will alter the column type. This might fail if data exists.
-- Safe approach: Drop column and re-add it.
ALTER TABLE roadmaps DROP COLUMN IF EXISTS embedding;
ALTER TABLE roadmaps ADD COLUMN embedding vector(384);

-- Create HNSW index for fast search
CREATE INDEX roadmaps_embedding_idx ON roadmaps USING hnsw (embedding vector_cosine_ops);


-- 3. Update FAQ table
-- -------------------
DROP INDEX IF EXISTS faq_embedding_idx;
ALTER TABLE faq DROP COLUMN IF EXISTS embedding;
ALTER TABLE faq ADD COLUMN embedding vector(384);

CREATE INDEX faq_embedding_idx ON faq USING hnsw (embedding vector_cosine_ops);


-- 4. Create/Update RPC Functions
-- ------------------------------

-- Function: Match Roadmaps
-- Drop legacy function first to avoid return type conflict
DROP FUNCTION IF EXISTS match_roadmaps(vector, int, float);
DROP FUNCTION IF EXISTS match_roadmaps(vector, int, double precision);

CREATE OR REPLACE FUNCTION match_roadmaps (
  query_embedding vector(384),
  match_count int DEFAULT 5,
  similarity_threshold float DEFAULT 0.5
) RETURNS TABLE (
  id uuid,
  title text,
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
    r.description,
    r.url,
    r.category,
    1 - (r.embedding <=> query_embedding) as similarity
  FROM roadmaps r
  WHERE 1 - (r.embedding <=> query_embedding) > similarity_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;


-- Function: Match FAQs
DROP FUNCTION IF EXISTS match_faqs(vector, int, float);
DROP FUNCTION IF EXISTS match_faqs(vector, int, double precision);

CREATE OR REPLACE FUNCTION match_faqs (
  query_embedding vector(384),
  match_count int DEFAULT 5,
  similarity_threshold float DEFAULT 0.5
) RETURNS TABLE (
  id uuid,
  question_ar text,
  answer_ar text,
  question_en text,
  answer_en text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    f.id,
    f.question_ar,
    f.answer_ar,
    f.question_en,
    f.answer_en,
    1 - (f.embedding <=> query_embedding) as similarity
  FROM faq f
  WHERE f.is_active = true
  AND 1 - (f.embedding <=> query_embedding) > similarity_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;
