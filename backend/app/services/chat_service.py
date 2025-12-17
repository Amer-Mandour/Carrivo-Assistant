"""
الخدمة الرئيسية لمعالجة المحادثات مع Language Detector المتقدم
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging
import re
import uuid
import traceback

from ..config import settings
from ..database import get_supabase
from .llm_service import LLMService
from .rag_service import RAGService
from .embedding_service import EmbeddingService
from .roadmap_service import RoadmapService
from ..utils.language_detector import language_detector, LanguageType

logger = logging.getLogger(__name__)

class ChatService:
    """خدمة معالجة المحادثات المتقدمة"""
    
    def __init__(self):
        self.llm = LLMService()
        self.rag = RAGService()
        self.embedding = EmbeddingService()
        self.roadmap_service = RoadmapService()
        self.supabase = get_supabase()
    
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        preferred_language: str = "auto"
    ) -> Dict:
        """
        معالجة رسالة المستخدم مع كشف اللغة المتقدم
        """
        try:
            # Generate session_id if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            logger.info("Starting ChatService.process_message")
            
            # 1. كشف اللغة المتقدم
            detected_lang, confidence = language_detector.detect_with_confidence(message)
            logger.info(f"Language detected: {detected_lang}")
            
            # 2. تحديد لغة الرد
            user_language = self._determine_response_language(detected_lang, preferred_language)
            logger.info(f"User language determined: {user_language}")
            
            # 3. جلب conversation history (زودنا من 5 إلى 8 للفهم الأحسن)
            conversation_history = await self._get_conversation_history(session_id, limit=8)
            logger.info(f"History retrieved: {len(conversation_history)} items")
            
            # 4. تحسين الاستعلام بناءً على السياق (Contextualization)
            refined_message = message
            if conversation_history:
                logger.info("Contextualizing query...")
                refined_message = await self.llm.contextualize_query(message, conversation_history)
            
            # 5. التحقق من طلب Roadmap (باستخدام الرسالة المحسنة)
            roadmap_query = await self._detect_roadmap_request(refined_message)
            
            # 6. البحث في المصادر
            context = []
            if roadmap_query:
                # استخدمنا الرسالة المحسنة للبحث
                roadmaps = await self.roadmap_service.search_roadmaps(refined_message, limit=3)
                
                if roadmaps:
                    context = self._format_roadmap_context(roadmaps)
                else:
                    return self._generate_fallback_response(
                        user_language, 
                        session_id,
                        detected_lang.value
                    )
            else:
                # بحث في الـ FAQ بالرسالة المحسنة
                faq_context = await self.rag.search_faqs(refined_message, user_language.value)
                context = faq_context
            
            # 7. توليد الرد
            response = await self.llm.generate_response(
                message=message,
                context=context,
                conversation_history=conversation_history,
                user_language=user_language,
                language=user_language.value
            )
            
            # 8. حفظ المحادثة
            await self._save_conversation(
                session_id=session_id,
                user_message=message,
                bot_response=response["text"],
                language=user_language.value
            )
            
            return {
                "response": response["text"],
                "session_id": session_id,
                "user_language": user_language.value,
                "detected_language": detected_lang.value,
                "language_confidence": confidence,
                "response_language": user_language.value,
                "is_egyptian": user_language == LanguageType.ARABIC_EGYPTIAN,
                "confidence": response.get("confidence", 0.9),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            traceback.print_exc()
            return self._generate_error_response(preferred_language, session_id)
    
    def _determine_response_language(
        self, 
        detected: LanguageType, 
        preferred: str
    ) -> LanguageType:
        """تحديد لغة الرد النهائية"""
        if preferred != "auto":
            try:
                return LanguageType(preferred)
            except ValueError:
                pass
        
        # استخدام اللغة المكتشفة
        if detected in [LanguageType.ARABIC_EGYPTIAN, LanguageType.ARABIC_FUSHA, LanguageType.ENGLISH]:
            return detected
        
        # افتراضي: المصرية
        return LanguageType.ARABIC_EGYPTIAN
    
    def _generate_fallback_response(
        self, 
        user_language: LanguageType, 
        session_id: str,
        detected_lang: str
    ) -> Dict:
        """توليد رد fallback عند عدم وجود roadmaps"""
        messages = {
            LanguageType.ARABIC_EGYPTIAN: "معلش يا باشا، مفيش رود ماب متاح للمجال ده دلوقتي.",
            LanguageType.ARABIC_FUSHA: "عذراً، لا يوجد رودماب متاح لهذا المجال حالياً.",
            LanguageType.ENGLISH: "Sorry, no roadmap available for this field right now."
        }
        
        return {
            "response": messages.get(user_language, messages[LanguageType.ARABIC_EGYPTIAN]),
            "session_id": session_id,
            "user_language": user_language.value,
            "detected_language": detected_lang,
            "response_language": user_language.value,
            "is_egyptian": user_language == LanguageType.ARABIC_EGYPTIAN,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_error_response(self, preferred_language: str, session_id: str) -> Dict:
        """توليد رد خطأ"""
        error_messages = {
            "ar_EG": "فيه مشكلة دلوقتي. حاول تاني.",
            "ar": "حدث خطأ. حاول مرة أخرى.",
            "en": "An error occurred. Try again."
        }
        
        target_lang = preferred_language
        if target_lang == "auto":
            target_lang = "ar_EG" # Default fallback
            
        return {
            "response": error_messages.get(target_lang, error_messages["ar_EG"]),
            "session_id": session_id,
            "user_language": preferred_language,
            "response_language": preferred_language,
            "is_egyptian": preferred_language == "ar_EG",
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """جلب آخر رسائل من المحادثة"""
        try:
            result = self.supabase.table("conversations")\
                .select("role, content")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            history = list(reversed(result.data)) if result.data else []
            return history
            
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return []
    
    async def _detect_roadmap_request(self, message: str) -> Optional[str]:
        """اكتشاف طلب roadmap"""
        roadmap_keywords = [
            r"(مسار|رود\s*ماب|خريطة|طريق)",
            r"(ازاي\s+اتعلم|كيف\s+اتعلم|عايز\s+اتعلم)",
            r"(roadmap|road\s*map|path|guide)",
            r"(how\s+to\s+learn|learning\s+path)"
        ]
        
        message_lower = message.lower()
        
        for pattern in roadmap_keywords:
            if re.search(pattern, message_lower):
                return message_lower
        
        return None
    
    def _format_roadmap_context(self, roadmaps: list) -> list:
        """تنسيق نتائج Roadmaps"""
        formatted = []
        for roadmap in roadmaps:
            formatted.append({
                "question_ar": f"ما هو مسار {roadmap['title']}؟",
                "answer_ar": f"{roadmap['description']}\n\nالرابط: {roadmap['url']}",
                "question_en": f"What is the {roadmap['title']} roadmap?",
                "answer_en": f"{roadmap['description']}\n\nLink: {roadmap['url']}"
            })
        return formatted
    
    async def _save_conversation(
        self,
        session_id: str,
        user_message: str,
        bot_response: str,
        language: str
    ):
        """حفظ المحادثة"""
        try:
            self.supabase.table("conversations").insert({
                "session_id": session_id,
                "role": "user",
                "content": user_message,
                "language": language,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            self.supabase.table("conversations").insert({
                "session_id": session_id,
                "role": "assistant",
                "content": bot_response,
                "language": language,
                "created_at": datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.warning(f"Failed to save conversation: {e}")