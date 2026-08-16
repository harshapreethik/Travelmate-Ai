"""
TravelMate AI — Core Gemini AI Service
Features zero-config auto-language detection, script-matching (e.g., Tanglish/Hinglish),
and robust multi-model failover.
"""

import logging
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-3.7-flash"

    def _get_system_instruction(self, destination: str) -> str:
        return (
            f"You are TravelMate AI, an expert real-time multilingual travel companion and cultural guide.\n"
            f"Context / Destination: {destination}\n\n"
            f"CORE LANGUAGE & SCRIPT RULES:\n"
            f"1. AUTOMATIC LANGUAGE DETECTION: Detect the user's language automatically. You support EVERY language worldwide (Telugu, Hindi, Tamil, Kannada, Spanish, French, Japanese, etc.).\n"
            f"2. SCRIPT & TRANSLITERATION MIRRORING:\n"
            f"   - If the user types in native script (e.g., తెలుగు / हिन्दी / தமிழ்), reply in that exact native script.\n"
            f"   - If the user types transliterated language (e.g., Telugu in English alphabet / 'Tanglish', Hindi in English / 'Hinglish'), reply in that EXACT SAME transliterated style.\n"
            f"   - If the user asks in English, reply in clear English.\n"
            f"3. FORMATTING: Use clean Markdown formatting (bullet points, bold text). Jump directly into the answer with NO conversational filler or markdown heading hashtags."
        )

    def generate_chat_response(
        self,
        user_message: str,
        destination: str = "Global / Any Destination"
    ) -> str:
        system_instruction = self._get_system_instruction(destination)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=2048,
            temperature=0.4
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
                    logger.info(f"Chat request with ({model}) [Attempt {attempt + 1}]")
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
        target_lang: str = "auto",
        destination: str = "Global / Any Destination"
    ) -> str:
        prompt = (
            f"You are TravelMate AI's universal smart travel translator.\n"
            f"Context / Destination: {destination}\n\n"
            f"Input Phrase: \"{phrase}\"\n\n"
            f"TASK:\n"
            f"1. Detect the input language and user intent.\n"
            f"2. If a target language is specified as '{target_lang}' (and not 'auto'), translate into '{target_lang}'. If 'auto', translate to the primary local language of the destination or to English if the input was non-English.\n"
            f"3. Provide the output strictly in this Markdown format:\n"
            f"* **Detected Input:** [Detected Language and Script]\n"
            f"* **Translation:** [Translated text in native script]\n"
            f"* **Phonetic Pronunciation:** [How to pronounce it using English letters]\n"
            f"* **Traveler Note / Etiquette:** [1 practical usage tip]"
        )

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=600
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
                    logger.info(f"Translating phrase with ({model})")
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