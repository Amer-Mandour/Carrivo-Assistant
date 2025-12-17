# 📚 API Documentation - Carrivo Assistant Chatbot

## 📋 Overview

**Carrivo Assistant** is a smart educational chatbot specialized in teaching programming, designed for Arab students with full support for the Egyptian dialect.

### 🎯 Key Features
- 💬 **Professional Interface** - Pure HTML/CSS/JS without frameworks
- 🧠 **Advanced AI** - Groq LLM (Llama 3.3 70B)
- 🔍 **RAG System** - Knowledge base search using pgvector
- 🌐 **Multilingual Support** - Modern Standard Arabic, Egyptian Dialect, English
- 🇪🇬 **Egyptian Dialect Understanding** - Automatic slang detection
- 💾 **Conversation History** - Supabase PostgreSQL
- 🚀 **Fast & Efficient** - FastAPI Backend
- 🎨 **Modern Design** - Gradient backgrounds & Glassmorphism

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (HTML/CSS/JS)                 │
│  - index.html: User Interface                               │
│  - script.js: App Logic                                     │
│  - style.css: Styling and Animations                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST API
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Routes Layer (chat.py)                             │   │
│  │  - POST /api/v1/chat                                │   │
│  │  - GET /api/v1/chat/languages                       │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     ↓                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Services Layer                                     │   │
│  │  - ChatService: Main Conversation Logic             │   │
│  │  - RAGService: FAQ Search                           │   │
│  │  - LLMService: Groq API Integration                │   │
│  │  - EmbeddingService: Text to Vector Conversion      │   │
│  │  - LanguageDetector: Language Detection            │   │
│  └──────────────────┬───────────────────────────────────┘   │
└────────────────────┼────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Database (Supabase PostgreSQL)                 │
│  - faq: Frequently Asked Questions with embeddings          │
│  - conversations: Chat History                             │
│  - pgvector: Semantic Search                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints - Full Documentation

### Base URL
```
http://localhost:8000
```

---

### 1️⃣ **GET /** - Home

**Description:** General API information

**URL:**
```
GET http://localhost:8000/
```

**Response:**
```json
{
  "message": "Welcome to Carrivo Assistant 🚀",
  "version": "1.0.0",
  "endpoints": {
    "chat": "/api/v1/chat",
    "docs": "/docs",
    "health": "/health"
  }
}
```

**Status Codes:**
- `200 OK` - Success

---

### 2️⃣ **GET /health** - System Health Check

**Description:** Check server and database status

**URL:**
```
GET http://localhost:8000/health
```

**Response (Success):**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-12T17:30:00.000000"
}
```

**Response (Error):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "timestamp": "2025-12-12T17:30:00.000000"
}
```

**Status Codes:**
- `200 OK` - System operating correctly

**Use Case:** 
- System monitoring
- Load balancer health checks
- DevOps monitoring

---

### 3️⃣ **POST /api/v1/chat** - Main Chat ⭐

**Description:** Send a message to the chatbot and receive a smart response

**URL:**
```
POST http://localhost:8000/api/v1/chat
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "How do I learn web development?",
  "session_id": "optional-session-id",
  "language": "auto"
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | string | ✅ Yes | - | User message |
| `session_id` | string | ❌ No | auto-generated | Session ID to maintain context |
| `language` | string | ❌ No | `"auto"` | Preferred language (`ar_EG`, `ar`, `en`, `auto`) |

**Response (Success):**
```json
{
  "response": "To learn web development, I'll start with the basics:\n\n1. **HTML** - Page Structure\n2. **CSS** - Styling & Colors\n3. **JavaScript** - Interactivity\n\nWhere would you like to start?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_language": "en",
  "response_language": "en",
  "is_egyptian": false,
  "confidence": 0.95,
  "timestamp": "2025-12-12T17:30:00.000000"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Chatbot response |
| `session_id` | string | Session ID (UUID) |
| `user_language` | string | Detected user language |
| `response_language` | string | Response language |
| `is_egyptian` | boolean | Is the user speaking Egyptian dialect? |
| `confidence` | float | Response confidence score (0.0 - 1.0) |
| `timestamp` | string | Response time (ISO 8601) |

**Response (Error):**
```json
{
  "detail": "Error processing message: [error message]"
}
```

**Status Codes:**
- `200 OK` - Processed successfully
- `422 Unprocessable Entity` - Invalid data
- `500 Internal Server Error` - Server error

**Examples:**

**Example 1: Question in Egyptian Arabic**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "عايز اتعلم Python، ابدأ منين؟",
    "language": "auto"
  }'
```

**Example 2: Question in English**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I learn React?",
    "language": "en"
  }'
```

**JavaScript Example (Frontend Integration):**
```javascript
async function sendMessage(message) {
  const response = await fetch('http://localhost:8000/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      session_id: localStorage.getItem('sessionId') || null,
      language: 'auto'
    })
  });
  
  const data = await response.json();
  
  // Save session_id for future messages
  localStorage.setItem('sessionId', data.session_id);
  
  return data;
}
```

---

### 4️⃣ **GET /api/v1/chat/languages** - Supported Languages

**Description:** Get list of supported languages

**URL:**
```
GET http://localhost:8000/api/v1/chat/languages
```

**Response:**
```json
{
  "supported_languages": [
    {
      "code": "ar_EG",
      "name": "Egyptian Arabic",
      "emoji": "🇪🇬"
    },
    {
      "code": "ar",
      "name": "Modern Standard Arabic",
      "emoji": "🇸🇦"
    },
    {
      "code": "en",
      "name": "English",
      "emoji": "🇺🇸"
    },
    {
      "code": "auto",
      "name": "Auto Detect",
      "emoji": "🤖"
    }
  ],
  "default": "ar_EG"
}
```

**Status Codes:**
- `200 OK` - Success

**Use Case:**
- Display language options in UI
- Check supported languages

---

### 5️⃣ **GET /docs** - Swagger UI Documentation

**Description:** Interactive API interface

**URL:**
```
GET http://localhost:8000/docs
```

**Features:**
- Test endpoints directly
- View schemas
- Interactive examples

---

### 6️⃣ **GET /redoc** - ReDoc Documentation

**Description:** Alternative cleaner documentation

**URL:**
```
GET http://localhost:8000/redoc
```

---

## 🔐 Authentication & Security

**Current Status:** No authentication (Development Mode)

**For Production:**
Recommended to add:
- API Keys
- JWT Tokens
- Rate Limiting
- CORS Configuration

---

## 📊 Data Models (Pydantic Schemas)

### ChatRequest
```python
{
  "message": str,           # Required
  "session_id": str | None, # Optional
  "language": str           # Optional, default: "auto"
}
```

### ChatResponse
```python
{
  "response": str,          # Bot response
  "session_id": str,        # UUID
  "user_language": str,     # ar_EG, ar, en
  "response_language": str, # ar_EG, ar, en
  "is_egyptian": bool,      # True/False
  "confidence": float,      # 0.0 - 1.0
  "timestamp": str          # ISO 8601
}
```

---

## 🗄️ Database Schema

### Table `faq`
```sql
CREATE TABLE faq (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  embedding VECTOR(1536),  -- OpenAI embeddings
  category TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Table `conversations`
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id TEXT NOT NULL,
  user_message TEXT NOT NULL,
  bot_response TEXT NOT NULL,
  user_language TEXT,
  response_language TEXT,
  is_egyptian BOOLEAN DEFAULT false,
  confidence FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 How to Run

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables (.env)
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

# Groq API
OPENROUTER_API_KEY=your_groq_api_key
OPENROUTER_MODEL=llama-3.3-70b-versatile

# App Settings
APP_ENV=development
DEBUG=true
```

### 3. Run Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Frontend
```bash
cd frontend
python run_server.py
```

Browser will open at: `http://localhost:8080`

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

Running on:
- **Backend:** `http://localhost:8000`
- **Frontend:** `http://localhost:8080`

---

## 🧪 Testing Examples

### Python (requests)
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/chat',
    json={
        'message': 'How do I learn JavaScript?',
        'language': 'auto'
    }
)

print(response.json())
```

### JavaScript (fetch)
```javascript
fetch('http://localhost:8000/api/v1/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'I want to learn React',
    language: 'auto'
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How to learn Python?","language":"auto"}'
```

---

## 🔧 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | FastAPI | Latest |
| **Frontend** | HTML5/CSS3/Vanilla JS | - |
| **Database** | Supabase (PostgreSQL) | Latest |
| **Vector DB** | pgvector | Latest |
| **LLM** | Groq (Llama 3.3 70B) | Latest |
| **Embeddings** | OpenAI | text-embedding-3-small |
| **Python** | 3.9+ | - |

---

## 📝 Important Notes for Integration Team

### 1. **CORS Configuration**
Backend is currently open to all origins:
```python
allow_origins=["*"]
```

**For Production:** Change `["*"]` to your domain:
```python
allow_origins=["https://yourwebsite.com"]
```

### 2. **Session Management**
- `session_id` is auto-generated if not sent
- Save `session_id` in `localStorage` to maintain context
- Each session is separate and independent

### 3. **Language Detection**
- Use `"auto"` for automatic detection
- System detects Egyptian dialect automatically
- You can force a language by setting `language`

### 4. **Error Handling**
Ensure to handle:
- Network errors
- 500 errors (server issues)
- 422 errors (validation)
- Timeout errors

### 5. **Rate Limiting**
Currently: 30 request/minute (adjustable in `config.py`)

### 6. **Response Time**
- Average: 2-5 seconds
- Depends on message length and query complexity
- Use loading indicators

---

## 🎨 Frontend Integration Guide

### HTML Structure
```html
<div id="chat-container">
  <div id="messages"></div>
  <form id="chat-form">
    <input type="text" id="message-input" />
    <button type="submit">Send</button>
  </form>
</div>
```

### JavaScript Integration
```javascript
const API_URL = 'http://localhost:8000/api/v1/chat';
let sessionId = localStorage.getItem('chatSessionId');

async function sendMessage(message) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        language: 'auto'
      })
    });
    
    if (!response.ok) throw new Error('Network error');
    
    const data = await response.json();
    
    // Save session for future chats
    sessionId = data.session_id;
    localStorage.setItem('chatSessionId', sessionId);
    
    // Display response
    displayMessage(data.response, 'bot');
    
    return data;
  } catch (error) {
    console.error('Error:', error);
    displayMessage('Sorry, an error occurred. Please try again.', 'error');
  }
}

// Event listener
document.getElementById('chat-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const input = document.getElementById('message-input');
  const message = input.value.trim();
  
  if (message) {
    displayMessage(message, 'user');
    sendMessage(message);
    input.value = '';
  }
});
```

---

## 🐛 Troubleshooting

### Issue: CORS Error
**Solution:**
```python
# In backend/app/main.py
allow_origins=["http://localhost:3000", "https://yoursite.com"]
```

### Issue: Database Connection Failed
**Solution:**
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- Verify pgvector extension is enabled
- Review migrations

### Issue: LLM Not Responding
**Solution:**
- Check `OPENROUTER_API_KEY`
- Ensure Groq account balance
- Try another model

---

## 📞 Contact & Support

- **GitHub:** [Amer-Mandour](https://github.com/Amer-Mandour)
- **Project:** roadmapChatbot
- **Version:** 1.0.0
- **Last Updated:** 2025-12-12

---

## 📄 License

MIT License - Free to use

---

**Made with ❤️ for Developers**
