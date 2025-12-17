"""
Final LLM Service with link hallucination prevention and general greetings
"""

import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import re
from typing import List, Dict, Optional
import logging
from ..config import settings
from ..utils.language_detector import LanguageType

logger = logging.getLogger(__name__)

class LLMService:
    """Final AI Service"""
    
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        # Use valid model
        self.model = "llama-3.1-8b-instant"
    
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        message: str,
        context: List[Dict],
        conversation_history: List[Dict] = None,
        user_language: LanguageType = LanguageType.ARABIC_EGYPTIAN,
        language: str = "auto"
    ) -> Dict:
        """Generate intelligent and clean response"""
        try:
            system_prompt = self._build_system_prompt(user_language)
            context_text = self._build_context_text(context, user_language)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                # Send last 2 messages to LLM to understand context
                for msg in conversation_history[-2:]:
                    # Ensure content is not None
                    content = msg.get("content") or ""
                    role = msg.get("role") or "user"
                    messages.append({"role": role, "content": content})
            
            # Extract available URLs from context for explicit instruction
            available_urls = self._extract_urls_from_context(context)
            url_warning = ""
            if available_urls:
                url_list = "\n".join([f"  - {url}" for url in available_urls])
                url_warning = f"\n\n⚠️ AVAILABLE URLS (USE ONLY THESE):\n{url_list}\n⚠️ DO NOT create, invent, or suggest any other URLs!"
            else:
                url_warning = "\n\n⚠️ NO URLS AVAILABLE - Do not provide any links!"
            
            # Build user prompt based on language
            if user_language == LanguageType.ENGLISH:
                user_prompt = f"""Context: {context_text if context_text else "None"}{url_warning}

Question: {message}

Answer intelligently:"""
            else:
                user_prompt = f"""Context: {context_text if context_text else "None"}{url_warning}

Question: {message}

Answer intelligently:"""
            
            messages.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            raw_text = response.choices[0].message.content
            cleaned_text = self._clean_foreign_characters(raw_text)
            
            # 🔒 CRITICAL: Validate URLs against context to prevent hallucination
            validated_text = self._validate_urls_against_context(cleaned_text, context)
            
            return {
                "text": validated_text,
                "confidence": 0.9,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"LLM error: {e}")
            
            error_messages = {
                LanguageType.ARABIC_EGYPTIAN: "معلش، فيه مشكلة. حاول تاني.",
                LanguageType.ARABIC_FUSHA: "عذراً، حدث خطأ.",
                LanguageType.ENGLISH: "Sorry, an error occurred."
            }
            
            return {
                "text": error_messages.get(user_language, error_messages[LanguageType.ARABIC_EGYPTIAN]),
                "confidence": 0.3,
                "tokens_used": 0
            }
    
    def _clean_foreign_characters(self, text: str) -> str:
        """Strong filtering for foreign characters"""
        
        forbidden_patterns = [
            r'[\u4e00-\u9fff]',
            r'[\u3040-\u309f]',
            r'[\u30a0-\u30ff]',
            r'[\uac00-\ud7af]',
            r'[\u0400-\u04ff]',
        ]
        
        cleaned = text
        for pattern in forbidden_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        forbidden_words = [
            '然而', '实际', '时间', '讨论', '的', '了',
            '실제', '시간',
            'の', 'は',
            'или', 'и',
        ]
        
        for word in forbidden_words:
            cleaned = cleaned.replace(word, '')
        
        replacements = {
            'coverage': '',
            'however': 'لكن',
            'moreover': '',
        }
        
        for eng, ar in replacements.items():
            cleaned = cleaned.replace(eng, ar)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        return cleaned
    
    def _validate_urls_against_context(self, text: str, context: List[Dict]) -> str:
        """
        🔒 CRITICAL SECURITY: Remove any URLs from response that are NOT in the database context.
        This prevents LLM hallucination of links.
        """
        logger.info(f"🔍 Validating URLs - Context items: {len(context) if context else 0}")
        
        if not context:
            # If no context, remove ALL URLs from response
            logger.warning("⚠️ No context provided - removing all URLs from response")
            return re.sub(r'https?://[^\s<>"]+', '[Link removed - not in database]', text)
        
        # Extract all valid URLs from context
        valid_urls = set()
        for item in context:
            logger.info(f"🔍 Context item keys: {item.keys()}")
            # Check all fields that might contain URLs
            for key, value in item.items():
                if value and isinstance(value, str):
                    # Find URLs in context values
                    found_urls = re.findall(r'https?://[^\s<>"]+', value)
                    if found_urls:
                        logger.info(f"🔍 Found URLs in '{key}': {found_urls}")
                    valid_urls.update(found_urls)
        
        logger.info(f"🔍 Valid URLs from database: {valid_urls}")
        
        # Find all URLs in the LLM response
        response_urls = re.findall(r'https?://[^\s<>"]+', text)
        
        if not response_urls:
            # No URLs in response, all good
            return text
        
        logger.info(f"🔍 URLs in LLM response: {response_urls}")
        
        # Helper to normalize URL for comparison
        def normalize_url(u):
            # 1. Remove trailing punctuation (.,;:!)] etc)
            u = re.sub(r'[.,;:!)]+$', '', u)
            # 2. Lowercase and strip trailing slash
            return u.rstrip('/').lower()
            
        normalized_valid_urls = {normalize_url(u) for u in valid_urls}
        logger.info(f"🔍 Valid URLs (normalized): {normalized_valid_urls}")
        
        # Check each URL in response
        validated_text = text
        for url in response_urls:
            # Normalize response URL
            norm_url = normalize_url(url)
            
            if norm_url not in normalized_valid_urls:
                # HALLUCINATED URL - Remove it!
                logger.warning(f"🚫 HALLUCINATED URL DETECTED AND REMOVED: {url} (Normalized: {norm_url})")
                validated_text = validated_text.replace(url, '[Link not available in database]')
        
        return validated_text
    
    def _extract_urls_from_context(self, context: List[Dict]) -> List[str]:
        """Extract all URLs from context for explicit instruction to LLM"""
        if not context:
            return []
        
        urls = set()
        for item in context:
            for key, value in item.items():
                if value and isinstance(value, str):
                    found_urls = re.findall(r'https?://[^\s<>"]+', value)
                    urls.update(found_urls)
        
        return list(urls)
    
    
    def _build_system_prompt(self, user_language: LanguageType) -> str:
        """Build final system prompt"""
        
        # Enhanced Arabic version with context understanding
        enhanced_arabic = """أنت "Carrivo Assistant" 🚀
مساعد ذكي ومصري، متخصص في مساعدة الطلبة والخريجين يختاروا طريقهم في مجال التكنولوجيا والبرمجة.

شخصيتك:
- بتتكلم عامية مصرية لطيفة ومحترفة (Semi-formal).
- صاحبك الفاهم اللي بينصحك من غير ما يعقدك.
- إجاباتك مباشرة ومن غير رغي كتير، إلا لو اتسألت عن شرح بالتفصيل.
- دمك خفيف بس رزين، ودايماً بتشجع المستخدم.

⛔ المصادر والروابط (مهم جداً):
- 🛑 ممنوع نهائياً تأليف أو اختراع أي لينكات (URLs).
- استخدم بس اللينكات الموجودة في الـ "Context" المرسل ليك.
- لو مفيش لينك في الـ Context، متكتبش لينكات من عندك. قول "المصدر مش متوفر".
- التزم بالبيانات اللي في قاعدة البيانات.

🎯 **قاعدة حرجة للـ Roadmaps:**
- لما المستخدم يطلب roadmap، ادي اللينك **فوراً** في أول رد.
- متشرحش الـ roadmap بالتفصيل قبل ما تدي اللينك.
- الصيغة المثالية: "تمام! ده الـ roadmap اللي هيساعدك: [اللينك]. لو عايز تفاصيل أكتر، قولي."
- **ممنوع** تشرح كل الـ phases قبل ما تدي اللينك.

قواعد مهمة جداً:
1. ⚠️ طول الرد: خليك في حدود 2-4 سطور لو بترد على كلام عادي. لو بتشرح توبيك كبير، خد راحتك وقسم الكلام نقط.
2. 🤯 ممنوع التكرار: لو لسه سائل سؤال، متكرروش. لو لسه قايل معلومة، متعدهاش. كمل على طول.
3. 🕵️ فهم السياق: اقرأ آخر كم شات عشان تفهم احنا بنتكلم في ايه. لو المستخدم قال "تمام" أو "ماشي"، ده معناه انه فهم، ادخل في اللي بعده.
4. 🇬🇧 المصطلحات: اكتب المصطلحات التقنية باللغة الإنجليزية زي ما هي (مثلاً: Backend, Frontend, DevOps) وسط الكلام العربي.

لو المستخدم طلب ترشيح مجالات (بناءً على شخصيته أو اهتماماته):
- الناس العملية (R): رشح لهم DevOps, Cyber Security, Mobile Dev.
- الناس اللي بتحب التفكير والتحليل (I): رشح لهم AI, Data Science, Backend.
- الناس المبدعة (A): رشح لهم Frontend, UI/UX, Game Dev.
- الناس الاجتماعية والقيادية (S/E): رشح لهم Product Management, DevRel.
- الناس المنظمة (C): رشح لهم QA, Testing, Data Analysis.

لو المستخدم تايه:
- بسّط له الدنيا. قوله يجرب أساسيات كل مجال ويشوف ايه اللي بيمشي مع دماغه.
- انصحه يبدأ بالأساسيات (CS Fundamentals) قبل ما يغرق في التولز.

أمثلة للطريقة اللي بترد بيها:
- "يا هلا! نورت Carrivo. قولي بتفكر في مجال ايه؟"
- "بص يا بطل، الـ Backend ده هو اللي بيحصل ورا الكواليس، زي المطبخ في المطعم، محدش شايفه بس هو الأساس."
- "لو انت محتار، جرب تتعلم HTML و CSS الأول، لو حسيت انك مبسوط يبقى كمل Frontend."

خليك ذكي، لماح، ومفيد. ومصري أصيل! 😉

⛔ خط أحمر (خارج النطاق):
أنت متخصص بس في: التعليم، البرمجة، الشغل، الـ Roadmaps، والتطوير المهني.
لو حد سألك في أي حاجة تانية (سياسة، دين، كورة، طب، طبخ.. الخ):
- اعتذر بلطف جداً.
- قوله إنك (AI Assistant) موجود عشان تساعده يبني مستقبله وشغله بس، ومش متخصص في الحاجات دي.
- صيغة مقترحة: "معلش يا صديقي، أنا تخصصي كله في التكنولوجيا والشغل والمسارات التعليمية عشان أقدر أفيدك صح. خليني أساعدك في كاريرك أحسن! 😄"
"""

        # Enhanced English version
        enhanced_english = """You are an educational assistant named "Carrivo Assistant".

⛔ SOURCES & LINKS (STRICT):
- 🛑 STRICTLY PROHIBITED to invent or hallucinate URLs.
- Use ONLY links provided in the "Context".
- If a link is not in the "Context", do NOT provide it. Say "I don't have this resource available."
- Stick faithfully to the provided Database Context.

🎯 **CRITICAL RULE for Roadmaps:**
- When user requests a roadmap, provide the link **IMMEDIATELY** in your first response.
- Do NOT explain all the phases/details before giving the link.
- Ideal format: "Here's the roadmap you need: [LINK]. Let me know if you'd like me to explain any part!"
- **NEVER** write a long explanation without the link first.

Basic Rules:
1. Reply in 2-4 lines for general conversation.
2. ⚠️ EXCEPTION: If user asks to "Explain", "Teach", "Detail", or "How to" -> IGNORE the length limit and explain in FULL DETAIL with examples and bullet points.
3. Use simple, friendly language.
4. Be direct and helpful.

⚠️ Context Awareness (Very Important):
- Read the last 3 messages before responding
- If you asked a question - the user is now answering it
- If you gave a link or info - don't repeat it
- If user said "okay" or "sure" - they understood, don't ask again
- Focus on the latest question only

⚠️ Recommendations based on Personality (RIASEC):
If the user mentions their personality type (R, I, A, S, E, C), understand it and recommend 3 jobs from this list:

[R] Realistic:
- DevOps, MLOps, Server-Side Game Developer, Cyber Security, Android, iOS

[I] Investigative:
- Backend, Full Stack, Data Analyst, AI Engineer, AI and Data Scientist, Machine Learning, Data Engineer, Blockchain, Software Architect, BI Analyst

[A] Artistic:
- Frontend, UI/UX Designer, Game Developer, Technical Writer

[S] Social:
- Developer Relations, Product Manager, Engineering Manager

[E] Enterprising:
- Product Manager, Engineering Manager, Developer Relations

[C] Conventional:
- QA, Data Analyst, BI Analyst

Example: If they say "I'm type I", tell them: "Since you're an analytical personality (Investigative), the best fields for you are: Backend, Data Analyst, AI Engineer."

⚠️ Handling Comparison & Confusion:
If user says "I'm confused between X and Y" or "I was recommended these, which one to pick?":
1. Explain the core difference simply (e.g., Frontend is visual, Backend is logic, Data is numbers).
2. Advise on how to choose: "Try exploring the basics of each, see which problem-solving style you enjoy more."
3. If asked about the "Correct Learning Path":
   - Start with Fundamentals, not just tools.
   - Practice heavily (Hands-on).
   - Follow a clear Roadmap.
   - Be patient, don't rush.

⚠️ Explaining Concepts (When asked to explain):
- Break down the concept into simple parts.
- Use analogies.
- List pros/cons if applicable.
- Mention key tools/technologies used in that field.
- Ensure the user truly understands the "Why" and "How".

Response Examples:

Example 1:
Question: "How are you"
Answer: "I'm doing great, thank you! I'm here to help you choose the right career path. What would you like to know today?"

Example 2:
Question: "Hello"
Answer: "Hello! Welcome. I'm ready to help you with anything related to your educational path."

Example 3:
Question: "I want to learn programming"
Answer: "Great! Programming is a wide field. Would you like to learn web design or server programming?"

Example 4:
Question: "I'm confused"
Answer: "That's totally normal! Tell me a bit about yourself and your interests, and I'll help you choose."

Example 5 (Context Understanding):
You asked: "Would you like Frontend or Backend?"
User replied: "Frontend"
Correct: "Excellent! Frontend focuses on user interfaces. You'll need to learn HTML, CSS, and JavaScript."
Wrong: "Would you like Frontend or Backend?" ❌ (Repetition!)

Remember: Be simple, clear, friendly, and DON'T repeat yourself!

⛔ OUT OF SCOPE (Strict Boundary):
You are specialized ONLY in: Education, Programming, Career Development, Roadmaps, and Tech Jobs.
If the user asks about ANYTHING else (Politics, Religion, Sports, Health, Cooking, etc.):
- Politely apologize.
- State that you are an AI Career Assistant and these topics are outside your expertise.
- Suggested phrasing: "I apologize, but I specialize only in technology and career guidance to help you build your future. Let's focus on your educational path! 😄"
"""
        
        prompts = {
            LanguageType.ARABIC_EGYPTIAN: enhanced_arabic,
            LanguageType.ARABIC_FUSHA: enhanced_arabic,
            LanguageType.ENGLISH: enhanced_english
        }
        
        return prompts.get(user_language, enhanced_arabic)
    
    async def contextualize_query(self, message: str, history: List[Dict]) -> str:
        """
        Rewrites the user's message to be a standalone search query based on history.
        Useful for "it", "this", "that" references.
        """
        try:
            if not history:
                return message
                
            # Build a simple history string
            history_text = ""
            for msg in history[-2:]: # Look at last 2 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
            
            prompt = f"""Conversation History:
{history_text}

User's Follow-up Input: "{message}"

Task: Rewrite the User's Input to be a full, standalone semantic search query that includes the specific topic from the history. 
If the input is already clear, return it as is.
If the input refers to "it" or "this", replace it with the actual subject (e.g., "roadmap for Frontend Game Dev").
Do NOT add extra words like "I want" or "Please". Just the core topic/query.

Standalone Query:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=60
            )
            
            refined_query = response.choices[0].message.content.strip()
            # Remove quotes if present
            refined_query = refined_query.replace('"', '').replace("'", "")
            
            logger.info(f"Refined Query: '{message}' -> '{refined_query}'")
            return refined_query
            
        except Exception as e:
            logger.error(f"Contextualization failed: {e}")
            return message

    def _build_context_text(self, context: List[Dict], user_language: LanguageType) -> str:
        """Build context text"""
        if not context:
            return ""
            
        text_parts = []
        for item in context:
            if user_language == LanguageType.ENGLISH:
                part = f"Q: {item.get('question_en', '')}\nA: {item.get('answer_en', '')}"
            else:
                part = f"س: {item.get('question_ar', '')}\nج: {item.get('answer_ar', '')}"
            text_parts.append(part)
            
        return "\n\n".join(text_parts)