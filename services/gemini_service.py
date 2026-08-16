"""
TravelMate AI — Core Gemini AI Service
Includes multi-model fallback, auto-retries, chat handling, and travel phrase translation.
"""

import logging
import time
from pathlib import Path
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
        self.active_model = "gemini-3.7-flash"

    def _get_system_instruction(self, destination: str, lang_code: str) -> str:
        language_name = Config.SUPPORTED_LANGUAGES.get(lang_code, "English")
        prompt_path = self.prompts_dir / "chat_prompt.txt"

        if prompt_path.exists():
            template = prompt_path.read_text(encoding="utf-8")
            return template.replace("{destination}", destination).replace("{language_name}", language_name)

        return (
            f"You are TravelMate AI, an expert travel assistant. "
            f"Context: {destination}. Respond clearly and engagingly in {language_name} using markdown formatting."
        )

    def generate_chat_response(
        self,
        user_message: str,
        lang_code: str = "en",
        destination: str = "Global / Any Destination"
    ) -> str:
        system_instruction = self._get_system_instruction(destination, lang_code)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=2048
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
                    logger.info(f"Calling Gemini ({model}) [Attempt {attempt + 1}] | Target: {destination}")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=user_message,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return response.text.strip()
                except Exception as e:
                    last_err = str(e)
                    if "503" in last_err or "UNAVAILABLE" in last_err:
                        time.sleep(1.5)
                        continue
                    else:
                        logger.warning(f"Model {model} failed: {last_err}")
                        break

        return f"⚠️ API Error: {last_err}"

    def translate_phrase(
        self,
        phrase: str,
        target_lang_code: str = "en",
        destination: str = "Global / Any Destination"
    ) -> str:
        language_name = Config.SUPPORTED_LANGUAGES.get(target_lang_code, "English")

        prompt = (
            f"You are an expert real-time travel translator and cultural guide.\n"
            f"Translate the following traveler phrase into {language_name} ({target_lang_code}).\n"
            f"Travel Destination / Context: {destination}\n\n"
            f"Original Phrase: \"{phrase}\"\n\n"
            f"Output strictly in the following Markdown format:\n"
            f"* **Translation:** [Translated phrase in {language_name} script]\n"
            f"* **Pronunciation (How to say it):** [Clear romanized phonetic guide for English speakers]\n"
            f"* **Cultural Tip / Politeness Note:** [1 brief sentence on tone, etiquette, or practical local use]"
        )

        config = types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=3000  # Increased to allow full menu translations without cutoff
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
                    logger.info(f"Translating with Gemini ({model}) to {language_name}")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return response.text.strip()
                except Exception as e:
                    last_err = str(e)
                    if "503" in last_err or "UNAVAILABLE" in last_err:
                        time.sleep(1.5)
                        continue
                    else:
                        logger.warning(f"Translation failed on {model}: {last_err}")
                        break

        return f"⚠️ Translation Error: {last_err}"


_gemini_service = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service