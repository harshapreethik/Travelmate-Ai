"""
TravelMate AI — Travel Translation Service
Translates phrases with auto-detection, romanized pronunciations, local etiquette,
and high-availability offline caching for hackathon demo resilience.
"""

import logging
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)

# Exact-match offline phrasebook for zero-latency fallback
COMMON_TRAVEL_PHRASES = {
    "how are you": {
        "Telugu": {
            "detected": "English (Auto-detected)",
            "translation": "మీరు ఎలా ఉన్నారు?",
            "phonetic": "Meeru ela unnaru?",
            "tip": "Use 'Meeru' for polite/respectful address with elders and locals."
        },
        "Hindi": {
            "detected": "English (Auto-detected)",
            "translation": "आप कैसे हैं?",
            "phonetic": "Aap kaise hain?",
            "tip": "Always use 'Aap' rather than 'Tum' for polite interaction."
        },
        "Tamil": {
            "detected": "English (Auto-detected)",
            "translation": "நீங்கள் எப்படி இருக்கிறீர்கள்?",
            "phonetic": "Neengal eppadi irukireerkal?",
            "tip": "A warm smile when asking builds quick rapport."
        },
        "Spanish": {
            "detected": "English (Auto-detected)",
            "translation": "¿Cómo estás? / ¿Cómo está usted?",
            "phonetic": "KOH-moh ehs-TAHS",
            "tip": "Use '¿Cómo está usted?' in formal shops and hotels."
        }
    },
    "where is the nearest hospital": {
        "Telugu": {
            "detected": "English (Auto-detected)",
            "translation": "దగ్గర్లోని ఆసుపత్రి ఎక్కడ ఉంది?",
            "phonetic": "Daggarloni aasupathri ekkada undhi?",
            "tip": "Show this text directly to auto or cab drivers for emergency routing."
        },
        "Hindi": {
            "detected": "English (Auto-detected)",
            "translation": "सबसे नजदीकी अस्पताल कहाँ है?",
            "phonetic": "Sabse nazdeeki aspatal kahan hai?",
            "tip": "Emergency services can also be reached on 108/112."
        }
    },
    "how much does this cost": {
        "Telugu": {
            "detected": "English (Auto-detected)",
            "translation": "దీని ఖరీదు ఎంత? నాకు బిల్లు ఇవ్వగలరా?",
            "phonetic": "Deeni khareedu entha? Naaku bill ivvagalaa-raa?",
            "tip": "Asking for a bill ensures transparent local pricing."
        },
        "Hindi": {
            "detected": "English (Auto-detected)",
            "translation": "इसकी कीमत कितनी है? क्या आप मुझे बिल दे सकते हैं?",
            "phonetic": "Iski keemat kitni hai? Kya aap mujhe bill de sakte hain?",
            "tip": "Useful in markets and retail shops."
        }
    }
}


class TranslationService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-2.5-flash"
        ]
        self.active_model = self.candidate_models[0]

    def translate_phrase(
        self,
        text: str,
        target_lang: str = "Telugu",
        source_lang: str = "auto",
        destination: str = "Global / Any Destination"
    ) -> dict:
        clean_text = text.strip()
        if not clean_text:
            return {
                "original_text": "",
                "target_language": target_lang,
                "translation_data": "* **Error:** Please provide valid text to translate."
            }

        clean_key = clean_text.lower().replace("?", "").replace(".", "").strip()
        target_clean = "Telugu" if "telugu" in target_lang.lower() else ("Hindi" if "hindi" in target_lang.lower() else target_lang)

        # 1. Exact Match Offline Phrasebook Check (Prevents partial substring hijack)
        if clean_key in COMMON_TRAVEL_PHRASES and target_clean in COMMON_TRAVEL_PHRASES[clean_key]:
            item = COMMON_TRAVEL_PHRASES[clean_key][target_clean]
            cached_md = (
                f"* **Detected Input:** {item['detected']}\n"
                f"* **Translation:** {item['translation']}\n"
                f"* **Phonetic Pronunciation:** {item['phonetic']}\n"
                f"* **Traveler Note / Etiquette:** {item['tip']}"
            )
            return {
                "original_text": clean_text,
                "target_language": target_clean,
                "translation_data": cached_md
            }

        # 2. Live Multilingual AI Translation via Active Models
        prompt = f"""
You are TravelMate AI's universal smart travel translator.

INPUT SENTENCE: "{clean_text}"
SOURCE LANGUAGE: {source_lang} (If 'auto', detect automatically from text, slang, or transliterated Tanglish/Hinglish).
TARGET LANGUAGE: {target_lang}
TRAVEL CONTEXT / DESTINATION: {destination}

STRICT LINGUISTIC RULES:
1. Detect the source language and user intent accurately.
2. Translate the COMPLETE sentence faithfully into {target_lang}.
3. SCRIPT INTEGRITY: Use 100% pure script of {target_lang}. NEVER mix Devanagari/Hindi letters into Telugu, Tamil, or Latin text.
4. Provide a clear Romanized phonetic pronunciation guide in plain English letters.
5. Provide 1 practical cultural etiquette or polite usage tip.

OUTPUT FORMAT STRICTLY IN MARKDOWN:
* **Detected Input:** [Detected Source Language and Intent]
* **Translation:** [Pure translated text in native script]
* **Phonetic Pronunciation:** [Clear romanized phonetic guide]
* **Traveler Note / Etiquette:** [1 short practical cultural/politeness tip]
"""

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=800
        )

        last_error = ""
        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Translating phrase with ({model}) to {target_lang} [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return {
                            "original_text": clean_text,
                            "target_language": target_lang,
                            "translation_data": response.text.strip()
                        }
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Translation failed on {model} (Attempt {attempt + 1}): {last_error}")
                    if any(code in last_error for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                        time.sleep(0.8)
                        continue
                    break

        return {
            "original_text": clean_text,
            "target_language": target_lang,
            "translation_data": f"* **Error:** Unable to complete translation.\n* **Details:** {last_error}"
        }


_translation_service = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service