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
        self.active_model = "gemini-2.5-flash"
        self.candidate_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        destination: str = "Global / Any Destination",
        target_lang: str = "English",
        user_query: str = ""
    ) -> str:
        # Normalize webp/octet-stream mime types
        safe_mime = mime_type if mime_type and mime_type.startswith("image/") else "image/jpeg"

        prompt = f"""
You are TravelMate AI's visual intelligence and OCR engine.
Context / Destination: {destination}
Target Translation Language: {target_lang}
User Instructions: {user_query if user_query else 'Analyze this image in detail for a traveler.'}

TASK:
1. Extract and transcribe all visible text from the image (menu items, prices, signboard directions, or landmark names).
2. If it is a food menu:
   - Categorize clearly into Vegetarian (🟢) and Non-Vegetarian (🔴) items.
   - List the dishes, key ingredients, and prices.
   - Translate the dish names and descriptions into {target_lang}.
3. If it is a signboard or landmark, provide historical context and visitor advice.
4. Format the output cleanly in Markdown with bold titles, clean bullet points, and pricing.
"""

        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Analyzing vision image with ({model}) [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type=safe_mime),
                            prompt
                        ]
                    )
                    if response and response.text:
                        self.active_model = model
                        return response.text.strip()
                except Exception as e:
                    logger.warning(f"Vision model {model} failed: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.2)
                        continue
                    break

        return (
            "### Menu & Visual Analysis\n\n"
            "* **Status:** Image processed.\n"
            "* **Note:** Visual service is temporarily busy. Please try uploading the image again in a moment."
        )


_image_service = None


def get_image_service() -> ImageService:
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service