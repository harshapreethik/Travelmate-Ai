"""
TravelMate AI — Travel Translation Service
Translates phrases with auto-detection, romanized pronunciations, and local etiquette notes.
"""

import logging
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-2.5-flash"
        self.candidate_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]

    def translate_phrase(
        self,
        text: str,
        target_lang: str = "Telugu",
        source_lang: str = "auto",
        destination: str = "Global / Any Destination"
    ) -> dict:
        # Handles both full names ("Telugu") and language codes ("te") safely
        target_name = Config.SUPPORTED_LANGUAGES.get(target_lang, target_lang) if hasattr(Config, 'SUPPORTED_LANGUAGES') else target_lang

        prompt = f"""
You are an expert real-time travel translator and cultural phonetician.

INPUT PHRASE: "{text}"
SOURCE LANGUAGE: {source_lang} (If 'auto', detect automatically from text, slang, or transliterated Tanglish/Hinglish).
TARGET LANGUAGE: {target_name}
TRAVEL CONTEXT / DESTINATION: {destination}

TASK:
1. Identify the input language and whether it was typed in transliteration (e.g. Tanglish/Hinglish) or native script.
2. Translate accurately into {target_name}.
3. Provide an English phonetic pronunciation guide so any traveler can speak it aloud effortlessly.
4. Add 1 short cultural or politeness tip for saying this phrase locally.

STRICT MARKDOWN OUTPUT FORMAT ONLY:
* **Detected Language:** [Identified language & script]
* **Translation ({target_name}):** [Accurate translation in {target_name} script]
* **Pronunciation (How to say it):** [Clear romanized phonetic guide for English speakers]
* **Traveler Tip / Etiquette:** [1 practical local etiquette note]
"""

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=600
        )

        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Translating phrase with ({model}) to {target_name} [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return {
                            "original_text": text,
                            "target_language": target_name,
                            "translation_data": response.text.strip()
                        }
                except Exception as e:
                    err = str(e)
                    logger.warning(f"Translation failed on {model} attempt {attempt + 1}: {err}")
                    if "503" in err or "UNAVAILABLE" in err:
                        time.sleep(1.2)
                        continue
                    break

        # Fallback if live model calls hit timeouts
        return {
            "original_text": text,
            "target_language": target_name,
            "translation_data": f"* **Translation ({target_name}):** {text}\n* **Pronunciation:** [Service busy - please retry in a few seconds]\n* **Traveler Tip:** Always verify key directions with local transit staff."
        }


_translation_service = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service