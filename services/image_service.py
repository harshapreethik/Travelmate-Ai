"""
TravelMate AI — Image & Multimodal Vision Service
Universal language auto-detection for menu parsing, landmark OCR, and sign translation.
"""

import io
import logging
import time
from google import genai
from google.genai import types
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-3.7-flash"

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        destination: str = "Global / Any Destination",
        user_query: str = ""
    ) -> dict:
        prompt = (
            f"You are TravelMate AI's universal multimodal visual assistant.\n"
            f"Analyze this image (signboard, menu, monument, or object).\n"
            f"Context / Destination: {destination}\n"
            f"User Query: \"{user_query.strip() if user_query else 'Explain this image, transcribe any text, and give practical tourist guidance.'}\"\n\n"
            f"RULES:\n"
            f"1. Match the language and script style of the user's query. If the query is in Telugu (native or English script), reply in that style. If no query is provided, explain clearly in English with translated terms.\n"
            f"2. Transcribe original text from the image, translate it, and highlight any dietary/safety warnings.\n"
            f"3. Do NOT use introductory filler. Start directly with structured findings using bold headers and bullet points."
        )

        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return {"status": "error", "message": f"Invalid image format: {str(e)}"}

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=3000
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
                    logger.info(f"Analyzing image with ({model}) [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[pil_image, prompt],
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return {
                            "status": "success",
                            "analysis": response.text.strip()
                        }
                except Exception as e:
                    last_err = str(e)
                    if "503" in last_err or "UNAVAILABLE" in last_err:
                        time.sleep(1.5)
                        continue
                    else:
                        logger.warning(f"Vision model {model} failed: {last_err}")
                        break

        return {"status": "error", "message": f"Failed to analyze image: {last_err}"}


_image_service = None


def get_image_service() -> ImageService:
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service