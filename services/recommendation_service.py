"""
TravelMate AI — Recommendation Engine Service
Generates structured venue matrices formatted for consumer travel UI.
"""

import json
import logging
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-3.7-flash"

    def get_recommendations(
        self,
        destination: str,
        interests: list,
        budget_level: str = "Moderate",
        traveller_type: str = "Solo"
    ) -> dict:
        interests_str = ", ".join(interests) if interests else "Sightseeing, Local Culture, Food"

        prompt = f"""
You are a live travel directory database engine.
Generate exactly 4 to 6 top spot recommendations for:
- City/Destination: {destination}
- Traveler Type: {traveller_type}
- Budget Level: {budget_level}
- Selected Categories: {interests_str}

STRICT JSON OUTPUT ONLY (no markdown code blocks, no intro text):
{{
  "destination_summary": "{destination} • {traveller_type} • {budget_level} Budget",
  "recommendations": [
    {{
      "name": "Exact Name of Place or Food Joint",
      "category": "Heritage / Food & Cafe / Nature / Bazaar / Adventure",
      "rating": 4.8,
      "reviews_count": "12.4k",
      "match_score": 96,
      "highlight": "1 short punchy sentence on the top attraction or dish here.",
      "best_time": "e.g., 4:00 PM - 7:00 PM",
      "approx_cost": "e.g., ₹150 or Free Entry",
      "duration": "e.g., 2 hrs",
      "local_tip": "1 practical tip (e.g., Buy tickets online to skip queue)."
    }}
  ]
}}
"""

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=2200,
            response_mime_type="application/json"
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
                    logger.info(f"Fetching structured spots with ({model}) [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        raw_json = response.text.strip()
                        if raw_json.startswith("```json"):
                            raw_json = raw_json[7:]
                        if raw_json.endswith("```"):
                            raw_json = raw_json[:-3]

                        parsed_data = json.loads(raw_json.strip())
                        self.active_model = model
                        return parsed_data
                except Exception as e:
                    logger.warning(f"Failed on {model}: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.5)
                        continue
                    break

        return {
            "destination_summary": f"{destination} Recommendations",
            "recommendations": []
        }


_recommendation_service = None


def get_recommendation_service() -> RecommendationService:
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service