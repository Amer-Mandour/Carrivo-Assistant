-- الجداول الأساسية للشات بوت المبسط

-- 1. جدول الأسئلة الشائعة (FAQ)
CREATE TABLE faq (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- النصوص العربية
    question_ar TEXT NOT NULL,
    question_egyptian TEXT, -- السؤال باللهجة المصرية
    answer_ar TEXT NOT NULL,
    answer_egyptian TEXT, -- الإجابة باللهجة المصرية
    
    -- النصوص الإنجليزية
    question_en TEXT,
    answer_en TEXT,
    
    -- التصنيف
    category VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    priority INTEGER DEFAULT 1,
    
    -- الحالة
    is_active BOOLEAN DEFAULT TRUE,
    
    -- التواريخ
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. جدول المسارات (مبسط)
CREATE TABLE roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- العنوان
    slug VARCHAR(200) UNIQUE NOT NULL,
    title_ar VARCHAR(255) NOT NULL,
    title_en VARCHAR(255),
    
    -- الوصف
    description_ar TEXT,
    description_en TEXT,
    
    -- التصنيف
    category VARCHAR(100) NOT NULL,
    difficulty VARCHAR(50) DEFAULT 'beginner',
    estimated_hours INTEGER,
    
    -- العلامات
    tags TEXT[] DEFAULT '{}',
    
    -- الحالة
    is_published BOOLEAN DEFAULT TRUE,
    
    -- المصدر
    source_url TEXT,
    
    -- التواريخ
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. جدول المحادثات (مبسط)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- معلومات الجلسة
    session_id VARCHAR(100) NOT NULL,
    
    -- الرسالة
    role VARCHAR(20) NOT NULL, -- 'user' أو 'assistant'
    content TEXT NOT NULL,
    
    -- اللغة
    language VARCHAR(10) DEFAULT 'ar_EG',
    is_egyptian BOOLEAN DEFAULT FALSE,
    
    -- التواريخ
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- إنشاء Indexes
CREATE INDEX idx_faq_category ON faq(category);
CREATE INDEX idx_faq_tags ON faq USING GIN(tags);
CREATE INDEX idx_roadmaps_category ON roadmaps(category);
CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_created ON conversations(created_at);

-- دالة تحديث updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_faq_updated_at BEFORE UPDATE ON faq
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roadmaps_updated_at BEFORE UPDATE ON roadmaps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();