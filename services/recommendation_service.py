"""
TravelMate AI — Recommendation Engine Service
Generates structured venue matrices formatted for consumer travel UI.
"""

import json
import logging
import random
import re
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
        
        # Primary high-quota model first, reliable flash models as auto-failovers
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash"
        ]
        self.active_model = self.candidate_models[0]

    def get_recommendations(
        self,
        destination: str,
        interests: list = None,
        budget_level: str = "Moderate",
        traveller_type: str = "Solo",
        custom_interests: str = ""
    ) -> dict:
        dest_clean = destination.strip() if destination and destination.strip() else "Global"
        combined_interests = ", ".join(interests) if interests else "Heritage, Food, Nature, Shopping, Nightlife"
        if custom_interests:
            combined_interests += f" | Custom Preferences: {custom_interests}"

        # Dynamic variation seeds to guarantee fresh, distinct spots on repeated clicks
        variety_seed = random.choice([
            "iconic sights mixed with authentic local neighborhood gems",
            "offbeat cultural spots, scenic viewpoints, and popular hangout spots",
            "top street food joints, vibrant markets, and historic architecture",
            "trending photo spots, local parks, and artisan boutiques"
        ])

        prompt = f"""
You are a live travel directory database engine.
Generate exactly 4 to 6 authentic, real-world, specific venue and spot recommendations located strictly in:
Destination: {dest_clean}
Traveler Persona: {traveller_type}
Budget Tier: {budget_level}
Categories & Activities: {combined_interests}
Focus: {variety_seed}

CRITICAL RULES:
1. Every recommended place must be a REAL, SPECIFIC, and EXISTING venue/landmark in {dest_clean}.
2. NEVER use generic templates like "Historic Core of {dest_clean}" or "Botanical Gardens in {dest_clean}".
3. Output strictly valid JSON matching this schema:

{{
  "destination_summary": "{dest_clean} • {traveller_type}",
  "recommendations": [
    {{
      "name": "Exact Real Place Name in {dest_clean}",
      "category": "Heritage / Food & Cafe / Nature / Shopping / Event",
      "rating": 4.8,
      "reviews_count": "12.4k",
      "match_score": 96,
      "highlight": "1 short punchy sentence on what makes this unique.",
      "best_time": "e.g., 4:00 PM - 7:00 PM",
      "approx_cost": "e.g., ₹150 or Free Entry",
      "duration": "e.g., 2 hrs",
      "local_tip": "1 practical insider tip."
    }}
  ]
}}
"""

        config = types.GenerateContentConfig(
            temperature=0.9,
            max_output_tokens=2500,
            response_mime_type="application/json"
        )

        last_error = None
        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Generating spots for '{dest_clean}' via {model} (Attempt {attempt + 1})...")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        raw = response.text.strip()
                        raw = re.sub(r"^```(?:json)?\s*", "", raw)
                        raw = re.sub(r"\s*```$", "", raw)

                        parsed = json.loads(raw.strip())
                        if "recommendations" in parsed and len(parsed["recommendations"]) > 0:
                            self.active_model = model
                            logger.info(f"Successfully generated {len(parsed['recommendations'])} spots using {model}")
                            return parsed
                except Exception as e:
                    logger.warning(f"Model {model} failed (Attempt {attempt + 1}): {e}")
                    last_error = e
                    # If rate limited (429) or overloaded (503), wait briefly then failover to the next candidate model
                    if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                        time.sleep(0.8)
                        continue
                    break

        logger.error(f"All candidate models failed for '{dest_clean}'. Last error: {last_error}")
        return {
            "destination_summary": f"{dest_clean} • {traveller_type}",
            "recommendations": []
        }


_recommendation_service = None


def get_recommendation_service() -> RecommendationService:
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service