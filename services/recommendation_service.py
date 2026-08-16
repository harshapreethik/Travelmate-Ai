"""
TravelMate AI — Recommendation Engine Service
Combines deterministic score-based JSON filtering with Gemini AI contextual reasoning.
"""

import json
import logging
from pathlib import Path
from config import Config
from services.gemini_service import get_gemini_service

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.data_file = Config.ATTRACTIONS_FILE
        self.attractions = self._load_attractions()

    def _load_attractions(self) -> list:
        """Loads attractions dataset from local ground-truth JSON."""
        try:
            if not Path(self.data_file).exists():
                logger.warning(f"Attractions file missing at {self.data_file}")
                return []
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load attractions data: {e}")
            return []

    def score_attraction(self, attraction: dict, preferences: dict) -> float:
        """
        Calculates a compatibility score (0.0 - 1.0) for an attraction against user preferences.
        """
        score = 0.0
        total_weights = 0.0

        # Preference 1: User Interests (Weight: 0.4)
        target_interests = preferences.get("interests", [])
        if target_interests:
            total_weights += 0.4
            matched = set(attraction.get("interests", [])).intersection(set(target_interests))
            if matched:
                score += 0.4 * (len(matched) / max(len(target_interests), 1))

        # Preference 2: Budget Match (Weight: 0.3)
        target_budget = preferences.get("budget_level")
        if target_budget:
            total_weights += 0.3
            if attraction.get("budget_level", "").lower() == target_budget.lower():
                score += 0.3
            elif attraction.get("budget_level", "").lower() == "budget":
                score += 0.2  # Budget options match almost everyone

        # Preference 3: Traveller Type Match (Weight: 0.2)
        traveller_type = preferences.get("traveller_type")
        if traveller_type:
            total_weights += 0.2
            if traveller_type in attraction.get("traveller_types", []):
                score += 0.2

        # Popularity Weight (Weight: 0.1)
        score += 0.1 * attraction.get("popularity_score", 0.8)

        return round(score, 2)

    def get_recommendations(
        self,
        destination: str = "Hyderabad",
        interests: list = None,
        budget_level: str = None,
        traveller_type: str = None,
        lang_code: str = "en",
        limit: int = 3
    ) -> dict:
        """
        Filters, ranks, and enriches top recommendations using deterministic scoring + Gemini reasoning.
        """
        interests = interests or []
        preferences = {
            "interests": interests,
            "budget_level": budget_level,
            "traveller_type": traveller_type
        }

        # Filter attractions by destination
        dest_attractions = [
            a for a in self.attractions 
            if a.get("destination", "").lower() == destination.lower()
        ]

        if not dest_attractions:
            # Fallback if specific city is not in JSON
            dest_attractions = self.attractions

        # Rank attractions using Python scoring
        scored_items = []
        for item in dest_attractions:
            match_score = self.score_attraction(item, preferences)
            item_copy = item.copy()
            item_copy["match_score"] = match_score
            scored_items.append(item_copy)

        # Sort descending by match score
        scored_items.sort(key=lambda x: x["match_score"], reverse=True)
        top_recommendations = scored_items[:limit]

        # Use Gemini AI to generate a natural personalized narrative summarizing these choices
        language_name = Config.SUPPORTED_LANGUAGES.get(lang_code, "English")
        ai_service = get_gemini_service()

        prompt_summary = (
            f"Act as a local travel expert in {destination}. "
            f"The user is a '{traveller_type or 'General'}' traveller with budget '{budget_level or 'Moderate'}' "
            f"interested in {', '.join(interests) if interests else 'top spots'}.\n\n"
            f"Here are the top ranked places selected for them:\n" +
            "\n".join([f"- {item['name']}: {item['description']}" for item in top_recommendations]) +
            f"\n\nIn {language_name}, write a brief, warm 3-bullet-point summary explaining why these choices fit their travel style and give 1 insider tip for visiting them."
        )

        ai_narrative = ai_service.generate_chat_response(
            user_message=prompt_summary,
            lang_code=lang_code,
            destination=destination
        )

        return {
            "destination": destination,
            "language": lang_code,
            "total_found": len(top_recommendations),
            "recommendations": top_recommendations,
            "ai_insights": ai_narrative
        }

# Singleton accessor
_recommendation_service = None

def get_recommendation_service() -> RecommendationService:
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service