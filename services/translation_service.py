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

# Instant offline phrasebook for zero-latency demo fallback
COMMON_TRAVEL_PHRASES = {
    "how are you": {
        "Telugu": {
            "detected": "English (Auto-detected)",
            "translation": "మీరు ఎలా ఉన్నారు? (Meeru ela unnaru?)",
            "phonetic": "Mee-roo eh-laa oon-naa-roo?",
            "tip": "Use 'Meeru' for polite/respectful address with elders and locals."
        },
        "Hindi": {
            "detected": "English (Auto-detected)",
            "translation": "आप कैसे हैं? (Aap kaise hain?)",
            "phonetic": "Aap kay-say hain?",
            "tip": "Always use 'Aap' rather than 'Tum' for polite interaction."
        },
        "Tamil": {
            "detected": "English (Auto-detected)",
            "translation": "நீங்கள் எப்படி இருக்கிறீர்கள்? (Neengal eppadi irukireerkal?)",
            "phonetic": "Neen-gal ep-pa-di ee-roo-kee-reer-gal?",
            "tip": "A warm smile when asking builds quick rapport."
        },
        "Spanish": {
            "detected": "English (Auto-detected)",
            "translation": "¿Cómo estás? / ¿Cómo está usted?",
            "phonetic": "KOH-moh ehs-TAHS",
            "tip": "Use '¿Cómo está usted?' in formal shops and hotels."
        }
    },
    "where is the nearest hospital or medical clinic?": {
        "Telugu": {
            "detected": "English (Auto-detected)",
            "translation": "దగ్గర్లోని ఆసుపత్రి లేదా మెడికల్ క్లినిక్ ఎక్కడ ఉంది?",
            "phonetic": "Daggarloni aasupathri leda medical clinic ekkada undhi?",
            "tip": "Show this text directly to auto or cab drivers for emergency routing."
        },
        "Hindi": {
            "detected": "English (Auto-detected)",
            "translation": "सबसे नजदीकी अस्पताल या मेडिकल क्लीनिक कहाँ है?",
            "phonetic": "Sabse nazdeeki aspatal ya medical clinic kahan hai?",
            "tip": "Emergency services can also be reached on 108/112."
        }
    },
    "how much does this cost? can you give me a bill?": {
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
        self.active_model = "gemini-3.5-flash-lite"
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.7-flash"
        ]

    def translate_phrase(
        self,
        text: str,
        target_lang: str = "Telugu",
        source_lang: str = "auto",
        destination: str = "Global / Any Destination"
    ) -> dict:
        clean_key = text.strip().lower().replace("?", "").replace(".", "")
        target_clean = "Telugu" if "telugu" in target_lang.lower() else ("Hindi" if "hindi" in target_lang.lower() else target_lang)

        # 1. Check Offline Phrasebook for Instant Zero-Quota Response
        for phr_key, lang_map in COMMON_TRAVEL_PHRASES.items():
            if clean_key in phr_key or phr_key in clean_key:
                if target_clean in lang_map:
                    item = lang_map[target_clean]
                    cached_md = (
                        f"* **Detected Language:** {item['detected']}\n"
                        f"* **Translation ({target_clean}):** {item['translation']}\n"
                        f"* **Pronunciation (How to say it):** {item['phonetic']}\n"
                        f"* **Traveler Tip / Etiquette:** {item['tip']}"
                    )
                    return {
                        "original_text": text,
                        "target_language": target_clean,
                        "translation_data": cached_md
                    }

        # 2. Live Multilingual AI Translation via Active Models
        prompt = f"""
You are TravelMate AI's universal smart travel translator and cultural phonetician.

INPUT PHRASE: "{text}"
SOURCE LANGUAGE: {source_lang} (If 'auto', detect automatically from text, slang, or transliterated Tanglish/Hinglish).
TARGET LANGUAGE: {target_lang}
TRAVEL CONTEXT / DESTINATION: {destination}

TASK:
1. Identify the input language and whether it was typed in transliteration (e.g. Tanglish/Hinglish) or native script.
2. Translate accurately into {target_lang}.
3. Provide an English phonetic pronunciation guide so any traveler can speak it aloud effortlessly.
4. Add 1 short cultural or politeness tip for saying this phrase locally.

STRICT MARKDOWN OUTPUT FORMAT ONLY:
* **Detected Language:** [Identified language & script]
* **Translation ({target_lang}):** [Accurate translation in native script]
* **Pronunciation (How to say it):** [Clear romanized phonetic guide in plain English letters]
* **Traveler Tip / Etiquette:** [1 practical local etiquette note]
"""

        last_error = ""
        for model in self.candidate_models:
            try:
                logger.info(f"Translating phrase with ({model}) to {target_lang}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if response and response.text:
                    self.active_model = model
                    return {
                        "original_text": text,
                        "target_language": target_lang,
                        "translation_data": response.text.strip()
                    }
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Translation failed on {model}: {last_error}")
                if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                    time.sleep(0.8)
                    continue
                continue

        # 3. Graceful Fallback if All API Quotas Are Exhausted
        return {
            "original_text": text,
            "target_language": target_lang,
            "translation_data": (
                f"* **Translation ({target_lang}):** {text}\n"
                f"* **Pronunciation:** [Live API rate limit reached]\n"
                f"* **Note:** Free tier daily limit reset in progress. Please retry shortly."
            )
        }


_translation_service = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service