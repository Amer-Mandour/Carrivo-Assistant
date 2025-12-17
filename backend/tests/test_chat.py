"""
اختبارات الوحدة للشات بوت
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """اختبار نقطة البداية"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_endpoint():
    """اختبار نقطة الصحة"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_languages_endpoint():
    """اختبار نقطة اللغات"""
    response = client.get("/api/v1/chat/languages")
    assert response.status_code == 200
    assert "supported_languages" in response.json()

@patch('app.services.llm_service.LLMService.generate_response')
def test_chat_endpoint(mock_llm):
    """اختبار نقطة المحادثة"""
    # إعداد mock
    mock_llm.return_value = {
        "text": "أهلاً وسهلاً!",
        "confidence": 0.9,
        "tokens_used": 50
    }
    
    request_data = {
        "message": "اهلا",
        "session_id": "test_session",
        "language": "ar_EG"
    }
    
    response = client.post("/api/v1/chat", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == "test_session"
    assert data["is_egyptian"] == True