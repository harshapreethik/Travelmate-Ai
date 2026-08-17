"""
TravelMate AI — Image & Vision Analysis Service
Extracts menus, signboards, and landmarks with multilingual translation.
"""

import logging
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-3.5-flash-lite"
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-3.7-flash"
        ]

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        destination: str = "Global / Any Destination",
        target_lang: str = "Telugu",
        user_query: str = ""
    ) -> str:
        safe_mime = mime_type.strip() if (mime_type and mime_type.startswith("image/")) else "image/jpeg"
        if "webp" in safe_mime:
            safe_mime = "image/webp"

        prompt = f"""
You are TravelMate AI's expert visual intelligence and OCR engine.
Context Destination: {destination}
Target Language for Output: {target_lang}
User Instructions: {user_query if user_query else 'Extract, transcribe, and translate all text, dishes, prices, and categories.'}

TASK:
1. Transcribe and translate all readable text from the image into {target_lang}.
2. If this is a food menu:
   - Categorize items clearly into Vegetarian (🟢) and Non-Vegetarian (🔴).
   - List dish names in {target_lang} with prices and brief descriptions.
3. If this is a signboard or landmark, provide historical background and visitor tips in {target_lang}.
4. Return clean, polished Markdown with bold titles and organized bullet points.
"""

        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=safe_mime)
        except Exception as err:
            logger.error(f"Failed to create image Part: {err}")
            return f"* **Error:** Could not process image ({err})."

        last_error = ""
        for model in self.candidate_models:
            try:
                logger.info(f"Analyzing vision image with ({model})")
                response = self.client.models.generate_content(
                    model=model,
                    contents=[image_part, prompt]
                )
                if response and response.text:
                    self.active_model = model
                    return response.text.strip()
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Vision model {model} failed: {last_error}")
                if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error:
                    time.sleep(1.0)
                    continue
                continue

        return f"* **Error:** Unable to complete visual analysis.\n* **Details:** {last_error}"


_image_service = None


def get_image_service() -> ImageService:
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service