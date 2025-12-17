"""
نماذج البيانات للمحادثة
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatRequest(BaseModel):
    """طلب محادثة من المستخدم"""
    message: str = Field(..., description="رسالة المستخدم")
    session_id: Optional[str] = Field(None, description="معرف الجلسة")
    language: Optional[str] = Field("auto", description="اللغة المفضلة (ar_EG, ar, en, auto)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "ازاي اتعلم برمجة ويب؟",
                "session_id": "session_123",
                "language": "ar_EG"
            }
        }

class ChatResponse(BaseModel):
    """استجابة المحادثة"""
    response: str = Field(..., description="رد البوت")
    session_id: str = Field(..., description="معرف الجلسة")
    user_language: str = Field(..., description="لغة المستخدم المكتشفة")
    response_language: str = Field(..., description="لغة الرد")
    is_egyptian: bool = Field(False, description="هل اللهجة مصرية؟")
    confidence: float = Field(0.9, description="درجة الثقة في الرد")
    timestamp: str = Field(..., description="وقت الرد")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "تمام! هشرحلك ازاي تبدأ...",
                "session_id": "session_123",
                "user_language": "ar_EG",
                "response_language": "ar_EG",
                "is_egyptian": True,
                "confidence": 0.95,
                "timestamp": "2024-12-04T22:00:00"
            }
        }
