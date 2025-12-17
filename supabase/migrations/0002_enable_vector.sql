-- تمكين امتداد pgvector (للنسخة الكاملة مستقبلاً)
CREATE EXTENSION IF NOT EXISTS vector;

-- جدول embeddings (للنسخة الكاملة)
CREATE TABLE IF NOT EXISTS roadmap_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id UUID REFERENCES roadmaps(id) ON DELETE CASCADE,
    embedding VECTOR(1536),
    content_type VARCHAR(50),
    content_text TEXT,
    language VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index للبحث السريع
CREATE INDEX IF NOT EXISTS idx_roadmap_embeddings ON roadmap_embeddings 
    USING ivfflat (embedding vector_cosine_ops);