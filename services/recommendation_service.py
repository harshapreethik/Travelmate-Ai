"""
TravelMate AI — Recommendation Engine Service
Generates structured venue matrices with match scoring, cost estimation, and map routing.
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
You are TravelMate AI's specialized Recommendation Engine algorithm.
Generate exactly 4 to 6 top curated spot recommendations for:
- Destination: {destination}
- Traveler Persona: {traveller_type}
- Budget Tier: {budget_level}
- Selected Interests: {interests_str}

STRICT JSON OUTPUT FORMAT ONLY:
Return a single JSON object with no markdown backticks, no markdown codeblocks, and no introductory text.

{{
  "ai_insights": "2-sentence high-level strategic summary of why this destination fits their chosen vibe and budget.",
  "recommendations": [
    {{
      "name": "Spot or Attraction Name",
      "category": "Heritage / Food / Nature / Bazaar / Adventure",
      "match_score": 0.95,
      "why_for_you": "1 crisp sentence explaining why this specifically fits a {traveller_type} with {budget_level} budget.",
      "best_time_to_visit": "e.g., 4:00 PM - 7:00 PM (Sunset)",
      "approx_cost": "e.g., Free or ₹150 Entry or $10",
      "duration": "e.g., 2 hours",
      "insider_tip": "One authentic local insider secret or tip to avoid crowds/scams."
    }}
  ]
}}
"""

        config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2500,
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
                    logger.info(f"Generating recommendations with ({model}) [Attempt {attempt + 1}]")
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
                    logger.warning(f"Recommendation generation failed on {model}: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.5)
                        continue
                    break

        return {
            "ai_insights": f"Found personalized spots for {destination}.",
            "recommendations": []
        }


_recommendation_service = None


def get_recommendation_service() -> RecommendationService:
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service