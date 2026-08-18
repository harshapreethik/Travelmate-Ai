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
        
        # Primary high-quota model first, active multimodal flash models as failovers
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-2.5-flash"
        ]
        self.active_model = self.candidate_models[0]

    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        destination: str = "Global / Any Destination",
        target_lang: str = "English",
        user_query: str = ""
    ) -> str:
        safe_mime = mime_type.strip() if (mime_type and mime_type.startswith("image/")) else "image/jpeg"
        if "webp" in safe_mime:
            safe_mime = "image/webp"

        prompt = f"""
You are TravelMate AI's expert visual intelligence and OCR engine.
Context Destination: {destination}
Target Language for Output: {target_lang}
User Instructions: {user_query if user_query else 'Extract, transcribe, and translate all text, warning signs, dishes, prices, and categories.'}

TASK:
1. Transcribe the original text visible in the image.
2. Translate all extracted text accurately into {target_lang}.
3. If this is a warning, danger, or advisory signboard:
   - Provide a clear, bold hazard/advisory explanation in {target_lang}.
   - Add a critical traveler safety tip.
4. If this is a food menu:
   - Categorize items into Vegetarian (🟢) and Non-Vegetarian (🔴).
   - If user instructions ask to 'identify veg' or similar, clearly emphasize and highlight the vegetarian options.
   - List items in {target_lang} with prices and descriptions.
5. Return clean, polished Markdown with bold titles and organized bullet points.
"""

        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=safe_mime)
        except Exception as err:
            logger.error(f"Failed to create image Part: {err}")
            return f"* **Error:** Could not process image ({err})."

        last_error = ""
        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Analyzing vision image with model ({model}) [Attempt {attempt + 1}]")
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
                    if any(code in last_error for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                        time.sleep(0.8)
                        continue
                    break

        return f"* **Error:** Unable to complete visual analysis.\n* **Details:** {last_error}"


_image_service = None


def get_image_service() -> ImageService:
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service