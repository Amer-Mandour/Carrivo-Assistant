"""
كاشف اللغة المتقدم لدعم LLM Service
"""

from enum import Enum
import re
from typing import Tuple

class LanguageType(str, Enum):
    ARABIC_EGYPTIAN = "ar_EG"
    ARABIC_FUSHA = "ar"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class AdvancedLanguageDetector:
    """كاشف اللغة المتقدم"""
    
    def __init__(self):
        # أنماط اللهجة المصرية
        self.egyptian_patterns = [
            r'\b(ازيك|إزيك|ازاى|إزاى|ايه|أيه)\b',
            r'\b(عامل ايه|عاملين ايه|عامل ايه ياسطا)\b',
            r'\b(تمام|ماشي|خلاص|بقا|يا عم|يا باشا)\b',
            r'\b(معلش|يا ريت|يعني|اصل|برضه|علشان)\b',
            r'\b(بص|اسمع|قول|روح|خش|جرب|شوف)\b',
            r'\b(فين|امتى|ليه|ازاي|كام|قد ايه)\b'
        ]
        
        # مصطلحات مصرية في التعليم
        self.egyptian_education_terms = [
            'كليه', 'جامعه', 'دكتور', 'مدرسه', 'معهد',
            'توجيهي', 'ثانويه', 'ابتدائي', 'اعدادي',
            'محاضره', 'امتحان', 'منهج', 'ماده', 'سكاشن'
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.egyptian_patterns]
    
    def detect_with_confidence(self, text: str) -> Tuple[LanguageType, float]:
        """
        كشف اللغة مع حساب درجة الثقة
        
        Returns:
            (نوع اللغة, درجة الثقة من 0 إلى 1)
        """
        if not text:
            return LanguageType.UNKNOWN, 0.0
        
        # Handle very short common English words manually
        text_lower = text.lower().strip()
        if text_lower in ['hi', 'ok', 'yes', 'no', 'hey', 'hello']:
            return LanguageType.ENGLISH, 1.0
        
        # 1. تحليل اللهجة المصرية
        egyptian_score = self._calculate_egyptian_score(text_lower)
        if egyptian_score > 0.6:
            return LanguageType.ARABIC_EGYPTIAN, egyptian_score
        
        # 2. تحليل النسبة بين الحروف العربية والإنجليزية
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        other_chars = len(re.findall(r'[^\w\s]', text))
        
        total_chars = max(arabic_chars + english_chars + other_chars, 1)
        
        arabic_ratio = arabic_chars / total_chars
        english_ratio = english_chars / total_chars
        
        # 3. تحديد اللغة بناءً على النسب
        # If explicitly mostly Arabic
        if arabic_ratio > 0.5:
            # تحقق من وجود كلمات مصرية في النص العربي
            if egyptian_score > 0.3:
                return LanguageType.ARABIC_EGYPTIAN, (arabic_ratio + egyptian_score) / 2
            return LanguageType.ARABIC_FUSHA, arabic_ratio
        
        # If explicitly mostly English
        elif english_ratio > 0.5:
            return LanguageType.ENGLISH, english_ratio
        
        # Mixed but significant presence
        elif arabic_ratio > 0.2 and english_ratio > 0.2:
            # نص مختلط
            mix_score = (arabic_ratio + english_ratio) / 2
            return LanguageType.MIXED, mix_score
        
        # Fallback: if more English than Arabic, assume English
        elif english_chars > arabic_chars:
            return LanguageType.ENGLISH, 0.4
            
        # Fallback: if more Arabic than English, assume Arabic
        elif arabic_chars > english_chars:
            return LanguageType.ARABIC_EGYPTIAN, 0.4
        
        else:
            return LanguageType.UNKNOWN, 0.5
    
    def _calculate_egyptian_score(self, text: str) -> float:
        """حساب درجة اللهجة المصرية"""
        if not text:
            return 0.0
        
        # 1. عدد الأنماط المطابقة
        pattern_matches = 0
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                pattern_matches += 1
        
        pattern_score = pattern_matches / len(self.compiled_patterns) if self.compiled_patterns else 0
        
        # 2. نسبة الكلمات المصرية التعليمية
        words = text.split()
        egyptian_education_words = sum(1 for word in words if word in self.egyptian_education_terms)
        education_score = egyptian_education_words / max(len(words), 1)
        
        # 3. الوزن المرجح
        total_score = (pattern_score * 0.7) + (education_score * 0.3)
        
        return total_score
    
    def get_language_display_name(self, language_type: LanguageType) -> str:
        """الحصول على الاسم المعروض للغة"""
        display_names = {
            LanguageType.ARABIC_EGYPTIAN: "اللهجة المصرية",
            LanguageType.ARABIC_FUSHA: "العربية الفصحى",
            LanguageType.ENGLISH: "الإنجليزية",
            LanguageType.MIXED: "مختلط (عربي + إنجليزي)",
            LanguageType.UNKNOWN: "غير معروف"
        }
        return display_names.get(language_type, "غير معروف")
    
    def should_respond_in_egyptian(self, detected_lang: LanguageType, user_preference: str) -> bool:
        """تحديد إذا كان يجب الرد باللهجة المصرية"""
        if user_preference == "ar_EG":
            return True
        
        if detected_lang == LanguageType.ARABIC_EGYPTIAN and user_preference in ["auto", "ar_EG"]:
            return True
        
        return False

# Singleton instance
language_detector = AdvancedLanguageDetector()