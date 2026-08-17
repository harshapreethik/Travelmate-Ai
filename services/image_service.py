"""
TravelMate AI — Image & Vision Analysis Service
Extracts menus, signboards, and landmarks with multilingual translation.
"""

import base64
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
        self.active_model = "gemini-2.0-flash"
        self.candidate_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        destination: str = "Global / Any Destination",
        target_lang: str = "Telugu",
        user_query: str = ""
    ) -> str:
        safe_mime = mime_type if (mime_type and "/" in mime_type) else "image/jpeg"

        prompt = f"""
You are TravelMate AI's expert visual intelligence and OCR engine.
Context / Destination: {destination}
Target Language for Output: {target_lang}
User Instructions: {user_query if user_query else 'Extract and translate all text, dishes, and categories.'}

TASK:
1. Extract and transcribe all visible items from the image (dishes, prices, ingredients, or signboards).
2. If this is a food menu:
   - Identify which items are strictly Vegetarian (🟢) vs Non-Vegetarian (🔴).
   - Translate all dish names, sections, and descriptions into {target_lang}.
   - Include prices alongside the items.
3. If this is a signboard or landmark, provide history and traveler tips in {target_lang}.
4. Output strictly in clean Markdown format with bold titles and structured bullet points.
"""

        # Build image part using multiple SDK-safe approaches
        image_part = None
        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=safe_mime)
        except Exception:
            try:
                image_part = types.Part(inline_data=types.Blob(data=image_bytes, mime_type=safe_mime))
            except Exception:
                image_part = {
                    "inline_data": {
                        "mime_type": safe_mime,
                        "data": base64.b64encode(image_bytes).decode("utf-8")
                    }
                }

        last_error = ""
        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Analyzing vision image with ({model}) [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[image_part, prompt]
                    )
                    if response and response.text:
                        self.active_model = model
                        return response.text.strip()
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Vision model {model} attempt {attempt + 1} failed: {last_error}")
                    if "503" in last_error or "UNAVAILABLE" in last_error:
                        time.sleep(1.5)
                        continue
                    break

        return f"* **Error:** Unable to complete visual analysis.\n* **Details:** {last_error}"


_image_service = None


def get_image_service() -> ImageService:
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service