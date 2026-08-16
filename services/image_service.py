"""
TravelMate AI — Image & Multimodal Vision Service
Fast, direct OCR and query-first image analysis without unnecessary fluff.
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
        target_lang: str = "en",
        destination: str = "Global / Any Destination",
        user_query: str = ""
    ) -> dict:
        language_name = Config.SUPPORTED_LANGUAGES.get(target_lang, "English")

        # Dynamic prompt prioritizing direct answers
        if user_query.strip():
            prompt = (
                f"You are TravelMate AI's direct visual assistant.\n"
                f"Analyze this image to answer the user's specific request: \"{user_query.strip()}\"\n"
                f"Target Language: {language_name}\n"
                f"Context / Destination: {destination}\n\n"
                f"RULES:\n"
                f"1. Answer the user's question directly in the first sentence. No introductory filler (e.g., do NOT say 'Based on the provided image...').\n"
                f"2. Group the findings clearly using concise Markdown bullet points and bold headers.\n"
                f"3. Include item names, translations, prices (if visible), and relevant dietary or travel warnings."
            )
        else:
            prompt = (
                f"You are TravelMate AI's direct visual assistant.\n"
                f"Analyze this travel image (signboard, menu, plaque, or landmark).\n"
                f"Target Language: {language_name}\n"
                f"Context / Destination: {destination}\n\n"
                f"Provide a clear, scannable response with NO introductory fluff:\n"
                f"* **Text & Translation:** [Key text transcribed and translated to {language_name}]\n"
                f"* **What It Means:** [1-2 concise sentences on what this is]\n"
                f"* **Traveler Action / Warning:** [Immediate advice on what to do or be cautious of]"
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
                    logger.info(f"Analyzing image with ({model}) [Attempt {attempt + 1}] | Query: {user_query}")
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