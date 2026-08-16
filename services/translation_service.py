"""
TravelMate AI — Travel Translation Service
Translates phrases with romanized pronunciations and local etiquette notes.
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
        self.active_model = "gemini-3.7-flash"

    def translate_phrase(
        self,
        text: str,
        target_lang: str = "en",
        destination: str = "Global / Any Destination"
    ) -> dict:
        language_name = Config.SUPPORTED_LANGUAGES.get(target_lang, "English")

        prompt = (
            f"You are an expert real-time travel translator and cultural guide.\n"
            f"Translate the following traveler phrase into {language_name} ({target_lang}).\n"
            f"Travel Destination / Context: {destination}\n\n"
            f"Original Phrase: \"{text}\"\n\n"
            f"Output strictly in the following Markdown format:\n"
            f"* **Translation:** [Translated phrase in {language_name} script]\n"
            f"* **Pronunciation (How to say it):** [Clear romanized phonetic guide for English speakers]\n"
            f"* **Cultural Tip / Politeness Note:** [1 brief sentence on tone, etiquette, or practical local use]"
        )

        config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=500
        )

        candidate_models = [
            self.active_model,
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-flash-latest"
        ]
        candidate_models = list(dict.fromkeys(candidate_models))

        last_err = ""
        for model in candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Translating phrase with ({model}) to {language_name}")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return {
                            "original_text": text,
                            "target_language": language_name,
                            "translation_data": response.text.strip()
                        }
                except Exception as e:
                    last_err = str(e)
                    if "503" in last_err or "UNAVAILABLE" in last_err:
                        time.sleep(1.5)
                        continue
                    else:
                        logger.warning(f"Translation failed on {model}: {last_err}")
                        break

        return {
            "original_text": text,
            "target_language": language_name,
            "translation_data": f"⚠️ Translation error: {last_err}"
        }


_translation_service = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service