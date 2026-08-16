"""
TravelMate AI — Itinerary Generation Service
"""

import logging
import time
from pathlib import Path
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)

class ItineraryService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-3.7-flash"

    def _build_itinerary_prompt(self, destination: str, num_days: int, budget: str, style: str, interests: list, lang_code: str) -> str:
        language_name = Config.SUPPORTED_LANGUAGES.get(lang_code, "English")
        interests_str = ", ".join(interests) if interests else "General Sightseeing, Local Cuisine"
        
        return (
            f"You are TravelMate AI, an expert travel planner.\n"
            f"Generate a complete, realistic {num_days}-day itinerary for {destination}.\n"
            f"Travel Style: {style} | Budget: {budget} | Interests: {interests_str}\n"
            f"Language: {language_name}\n\n"
            f"Format the itinerary clearly using:\n"
            f"- **Day X: [Theme]**\n"
            f"  - **Morning:** [Activities, places, timings]\n"
            f"  - **Afternoon:** [Lunch spots, sightseeing]\n"
            f"  - **Evening:** [Sunset views, dinner, nightlife/culture]\n\n"
            f"Include authentic restaurant recommendations and practical travel tips."
        )

    def generate_itinerary(
        self,
        destination: str = "Hyderabad",
        num_days: int = 2,
        budget_level: str = "Moderate",
        traveller_type: str = "Solo",
        interests: list = None,
        lang_code: str = "en"
    ) -> dict:
        prompt = self._build_itinerary_prompt(
            destination=destination,
            num_days=num_days,
            budget=budget_level,
            style=traveller_type,
            interests=interests or [],
            lang_code=lang_code
        )

        config = types.GenerateContentConfig(
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

        for model in candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Generating itinerary with {model} for {destination} ({num_days} days)")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return {
                            "destination": destination,
                            "num_days": num_days,
                            "itinerary": response.text.strip()
                        }
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.5)
                        continue
                    logger.warning(f"Itinerary model {model} failed: {e}")
                    break

        return {
            "destination": destination,
            "num_days": num_days,
            "itinerary": "Failed to generate complete itinerary. Please try again."
        }

_itinerary_service = None

def get_itinerary_service() -> ItineraryService:
    global _itinerary_service
    if _itinerary_service is None:
        _itinerary_service = ItineraryService()
    return _itinerary_service