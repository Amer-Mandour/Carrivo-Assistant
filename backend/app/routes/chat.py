"""
Chat API Endpoint
"""

from fastapi import APIRouter, HTTPException
from typing import Dict

from ..models.chat import ChatRequest, ChatResponse
from ..services.chat_service import ChatService

router = APIRouter(tags=["Chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint
    
    **Features:**
    - Supports Egyptian dialect
    - Supports Arabic and English
    - Auto language detection
    - Smart response based on FAQs
    
    **Example:**
    ```json
    {
        "message": "How do I learn web dev?",
        "session_id": "session_123",
        "language": "en"
    }
    ```
    """
    try:
        chat_service = ChatService()
        
        result = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            preferred_language=request.language
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

@router.get("/chat/languages")
async def get_supported_languages() -> Dict:
    """Get supported languages"""
    return {
        "supported_languages": [
            {"code": "ar_EG", "name": "Egyptian Arabic", "emoji": "🇪🇬"},
            {"code": "ar", "name": "Modern Standard Arabic", "emoji": "🇸🇦"},
            {"code": "en", "name": "English", "emoji": "🇺🇸"},
            {"code": "auto", "name": "Auto Detect", "emoji": "🤖"}
        ],
        "default": "ar_EG"
    }