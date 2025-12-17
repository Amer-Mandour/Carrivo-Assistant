# 🚀 Carrivo Assistant - Your Personal Learning Guide

A smart educational chatbot for learning programming that understands Egyptian dialect and English, guiding you to the right career paths.

## 🌟 Key Features

- 💬 **Professional Chat Interface** - HTML/CSS/JS with modern design (RTL Supported)
- 🧠 **Advanced AI** - Powered by Mixtral-8x7b via Groq
- 🇪🇬 **Egyptian Dialect Support** - Natural and smooth responses 100%
- 🔄 **Contextual Memory** - Understands conversation context and doesn't repeat itself
- 🔍 **RAG System** - For searching the knowledge base
- 🌐 **Bilingual Support** - Arabic (Egyptian/Standard) & English
- 💾 **Chat History** - Supabase Database
- 🚀 **Fast & Efficient** - FastAPI Backend
- 🎨 **Modern Design** - Gradient backgrounds & Animations

## 📁 Project Structure

```
roadmap-chatbot/
│
├── .env                         # API Keys (Groq/Supabase)
├── .env.example                 # Example keys
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # For local development
│
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── main.py              # Entry point
│   │   ├── config.py            # Settings (Mixtral Default)
│   │   ├── database.py          # Supabase client
│   │   ├── models/              # Pydantic models
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── chat_service.py  # Context & Memory Logic
│   │   │   ├── llm_service.py   # Groq Integration
│   │   │   ├── rag_service.py
│   │   │   └── roadmap_service.py
│   │   └── utils/               # Utilities
│   │       ├── logger.py
│   │       └── language_detector.py
│   └── tests/
│
├── frontend/                    # HTML/CSS/JS UI
│   ├── index.html               # Main interface
│   ├── style.css                # Styling
│   ├── script.js                # Logic
│   └── run_server.py            # Simple HTTP server
│
├── supabase/                    # Database
│   ├── migrations/
│   │   ├── 0001_initial_schema.sql
│   │   └── 0002_enable_vector.sql
│   └── seed.sql
│
└── docker/                      # Docker configs
```

## 🚀 Installation & Setup

### Prerequisites

- Python 3.9+
- Supabase Account
- OpenRouter API Key or Groq API Key

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Configure Keys

Copy `.env.example` to `.env` and add your keys:

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

# OpenRouter or Groq
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### 3️⃣ Setup Database

Run migrations in Supabase:
- Open Supabase Dashboard
- Go to SQL Editor
- Run files in `supabase/migrations/` in order
- Run `supabase/seed.sql` to add demo data

### 4️⃣ Run Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5️⃣ Run Frontend (HTML/CSS/JS)

```bash
cd frontend
python run_server.py
```

The browser will open automatically at: `http://localhost:8080`

## 🐳 Run with Docker

```bash
docker-compose up --build
```

Access:
- Backend at: `http://localhost:8000`
- Frontend at: `http://localhost:8080`

## 📡 API Endpoints

### POST /api/v1/chat

Send a message to the chatbot

**Request:**
```json
{
  "message": "How do I learn web dev?",
  "session_id": "optional-session-id",
  "language": "auto"
}
```

**Response:**
```json
{
  "response": "To learn web dev...",
  "session_id": "session-123",
  "language": "en",
  "sources": [...]
}
```

### GET /api/v1/chat/languages

Get supported languages

**Response:**
```json
{
  "supported_languages": [
    {"code": "ar_EG", "name": "Egyptian Arabic", "emoji": "🇪🇬"},
    {"code": "ar", "name": "Standard Arabic", "emoji": "🇸🇦"},
    {"code": "en", "name": "English", "emoji": "🇺🇸"},
    {"code": "auto", "name": "Auto Detect", "emoji": "🤖"}
  ],
  "default": "ar_EG"
}
```

### GET /health

System health check

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: Supabase (PostgreSQL + pgvector)
- **AI**: OpenRouter/Groq (Multiple LLM Models)
- **Embeddings**: OpenAI Embeddings
- **Deployment**: Docker, Docker Compose

## 🎨 Interface Features

- ✨ Modern design with Gradient backgrounds
- 🌓 Glassmorphism effects
- 🎭 Smooth animations & transitions
- 📱 Responsive design
- 🎯 RTL support for Arabic
- ⌨️ Keyboard shortcuts (Ctrl+K to focus input)
- 💬 Beautiful Message bubbles
- ⏱️ Timestamp for each message
- 🔄 Loading states

## 📝 Notes

- Ensure `pgvector` extension is enabled in Supabase
- You can change the LLM model in `backend/app/config.py` or `.env`
- To add new FAQs, edit `supabase/seed.sql`
- The interface supports Auto-detection for language (Egyptian/Standard Arabic/English)

## 🤝 Contributing

Contributions are welcome! Open an issue or pull request.

## 📄 License

MIT License

---

Made with ❤️ by Amer Mandour