# 📋 Carrivo Assistant - Project Brief

## 🎯 نظرة عامة على المشروع

**Carrivo Assistant** هو chatbot تعليمي ذكي مصمم لمساعدة الطلاب والخريجين في اختيار مسارهم المهني في مجال التكنولوجيا والبرمجة.

### المميزات الرئيسية:
- 🇪🇬 دعم اللهجة المصرية والعربية الفصحى والإنجليزية
- 🤖 استخدام Mixtral-8x7b-32768 عبر Groq API
- 💾 قاعدة بيانات Supabase (PostgreSQL + pgvector)
- 🔍 نظام RAG للبحث في المعرفة
- 💬 واجهة HTML/CSS/JS بسيطة وجميلة

---

## 🏗️ البنية المعمارية

### Backend (FastAPI)
```
backend/
├── app/
│   ├── main.py              # Entry point
│   ├── config.py            # Settings (Mixtral model)
│   ├── database.py          # Supabase client
│   ├── models/              # Pydantic models
│   ├── routes/
│   │   └── chat.py          # Chat endpoint
│   ├── services/
│   │   ├── chat_service.py      # Conversation logic
│   │   ├── llm_service.py       # Groq/Mixtral integration
│   │   ├── rag_service.py       # RAG search
│   │   ├── embedding_service.py # Embeddings (384-dim)
│   │   └── roadmap_service.py   # Roadmap search
│   └── utils/
│       ├── logger.py
│       └── language_detector.py
```

### Frontend (HTML/CSS/JS)
```
frontend/
├── index.html      # Main UI
├── style.css       # Styling
├── script.js       # Logic
└── run_server.py   # Simple HTTP server
```

### Database (Supabase)
```
supabase/
├── migrations/
│   ├── 0001_initial_schema.sql
│   ├── 0002_enable_vector.sql
│   ├── 0003_add_vector_embeddings.sql
│   ├── 0004_update_to_multilingual_embeddings.sql
│   └── fix_embeddings_384_v2.sql  # ✅ Current schema
└── seed.sql
```

---

## 🔄 كيف يعمل RAG System

### 1. **Embeddings Storage**
- يستخدم `pgvector` extension في Supabase
- الأبعاد: **384 dimensions** (من model: `paraphrase-multilingual-MiniLM-L12-v2`)
- الجداول:
  - `roadmaps` (title, description, url, category, **embedding**)
  - `faq` (question_ar, answer_ar, question_en, answer_en, **embedding**)

### 2. **Search Strategy (Hybrid)**
```
User Query
    ↓
1. Generate Embedding (384-dim)
    ↓
2. Try RPC Vector Search (Supabase)
   - match_roadmaps(query_embedding, match_count, similarity_threshold)
   - match_faqs(query_embedding, match_count, similarity_threshold)
    ↓
3. Fallback: Client-side Vector Search
   - Fetch all data
   - Calculate cosine similarity locally
    ↓
4. Last Resort: Keyword/Fuzzy Matching
   - Simple text overlap
```

### 3. **RPC Functions في Supabase**
```sql
-- Match Roadmaps
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

-- Match FAQs
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
```

---

## 🤖 LLM Integration (Mixtral)

### Configuration
- **Model**: `mixtral-8x7b-32768`
- **API**: Groq (https://api.groq.com/openai/v1)
- **Temperature**: 0.7
- **Max Tokens**: 800

### System Prompt Features
- شخصية مصرية ودودة
- ردود قصيرة (2-4 سطور) إلا للشروحات
- منع تكرار المعلومات
- فهم السياق من آخر رسائل
- منع اختراع روابط (Link Hallucination Prevention)
- التخصص فقط في التعليم والبرمجة

---

## 🔧 المشكلة الحالية

### ❌ Issue: `[Errno 22] Invalid argument`

**السبب المحتمل:**
- مشكلة في تحميل `sentence-transformers` model على Windows
- الـ model بيحاول يكتب في cache path فيه مشكلة
- الـ request بياخد timeout طويل جداً

**الحلول المجربة:**
1. ✅ تحديد `cache_folder` يدوياً
2. ✅ تعطيل الـ embedding service مؤقتاً
3. ⏳ استخدام OpenAI embeddings بدلاً من local model

**الحل المقترح:**
استخدام OpenAI text-embedding-3-small (512 dimensions) أو text-embedding-ada-002 (1536 dimensions) عبر Groq/OpenRouter API بدلاً من الـ local model.

---

## 📊 Data Flow

```
User Message
    ↓
Frontend (script.js)
    ↓
POST /api/v1/chat
    ↓
ChatService.process_message()
    ├─→ Language Detection
    ├─→ Get Conversation History
    ├─→ Contextualize Query (LLM)
    ├─→ Detect Roadmap Request?
    │   ├─ Yes → RoadmapService.search_roadmaps()
    │   │         ├─→ EmbeddingService.generate_embedding()
    │   │         ├─→ Supabase RPC: match_roadmaps()
    │   │         └─→ Fallback: Fuzzy Search
    │   └─ No  → RAGService.search_faqs()
    │             ├─→ EmbeddingService.generate_embedding()
    │             ├─→ Supabase RPC: match_faqs()
    │             └─→ Fallback: Keyword Search
    ↓
LLMService.generate_response()
    ├─→ Build System Prompt
    ├─→ Build Context from RAG results
    ├─→ Send to Mixtral (Groq API)
    └─→ Clean Response
    ↓
Save to Supabase (conversations table)
    ↓
Return Response to Frontend
```

---

## 🚀 كيفية التشغيل

### 1. Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend
```bash
cd frontend
python run_server.py
```

### 3. Access
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ✅ التحديثات المنفذة

1. ✅ تغيير الموديل من `llama3-8b-8192` إلى `mixtral-8x7b-32768`
2. ✅ إصلاح مسارات التشغيل على Windows في `embedding_service.py`
3. ✅ تنفيذ `run_in_executor` لتشغيل توليد الـ Embeddings في خيط منفصل (Thread) لتجنب حظر السيرفر
4. ✅ التأكد من عمل RAG System مع Supabase

---

## 📝 الخطوات التالية والملاحظات

1. **الأداء (Performance):**
   - توليد الـ Embeddings محلياً (CPU) قد يستغرق وقتاً (5-15 ثانية) لأول مرة.
   - تم حل مشكلة الـ Timeout باستخدام Multithreading.

2. **اختبار RAG:**
   - تم التحقق من عمل الـ Embeddings باستخدام سكريبت منفصل.
   - السيرفر يعمل الآن ويستجيب للطلبات.

---

**Last Updated**: 2025-12-17
**Status**: ✅ Operational (Embeddings fixed with Multithreading)
