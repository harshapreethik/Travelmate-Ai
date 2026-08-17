"""
TravelMate AI — Itinerary Planning Service
Generates structured day-by-day itineraries with explicit food/meal planning and custom routine integration.
"""

import json
import logging
import re
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


def _clean_slot(slot, fallback_activity="Sightseeing"):
    """Guarantees that each morning/afternoon/evening block is a valid dict with expected keys."""
    if isinstance(slot, dict):
        return {
            "activity": slot.get("activity") or slot.get("name") or fallback_activity,
            "description": slot.get("description") or slot.get("details") or "Explore local highlights.",
            "duration": slot.get("duration") or "2.5 hrs"
        }
    elif isinstance(slot, str) and slot.strip():
        return {
            "activity": slot.strip(),
            "description": "Explore local highlights.",
            "duration": "2.5 hrs"
        }
    return {
        "activity": fallback_activity,
        "description": "Explore local highlights.",
        "duration": "2.5 hrs"
    }


def _clean_dining(dining):
    """Guarantees breakfast, lunch, and dinner keys exist."""
    if isinstance(dining, dict):
        return {
            "breakfast": dining.get("breakfast") or "Traditional local breakfast & morning chai/coffee",
            "lunch": dining.get("lunch") or "Regional specialty lunch & thali",
            "dinner": dining.get("dinner") or "Signature dining or street food market"
        }
    elif isinstance(dining, str) and dining.strip():
        return {
            "breakfast": "Traditional morning breakfast",
            "lunch": dining.strip(),
            "dinner": "Signature local dinner"
        }
    return {
        "breakfast": "Traditional local breakfast",
        "lunch": "Regional lunch specialty",
        "dinner": "Signature local dinner"
    }


class ItineraryService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = "gemini-2.5-flash"

    def generate_itinerary(
        self,
        destination: str,
        num_days: int = 2,
        budget_level: str = "₹5,000",
        traveller_type: str = "Solo Explorer",
        selected_places: list = None,
        custom_schedule: str = "",
        **kwargs
    ) -> dict:
        extra_prompts = []
        if selected_places and len(selected_places) > 0:
            places_list_str = ", ".join(selected_places)
            extra_prompts.append(f"- MUST-VISIT PLACES FROM USER DISCOVERY: {places_list_str} (Incorporate these directly into the daily schedule).")
        if custom_schedule:
            extra_prompts.append(f"- USER CUSTOM ROUTINES & EVENTS TO INTEGRATE: {custom_schedule} (e.g., gym sessions, live shows, night cafes).")

        extras_str = "\n".join(extra_prompts)

        prompt = f"""
You are an expert travel logistics architect and culinary planner.
Generate a cohesive, scheduled day-by-day itinerary including explicit meal plans for:
- Destination: {destination}
- Duration: {num_days} Days
- Budget: {budget_level}
- Traveler Persona: {traveller_type}
{extras_str}

STRICT JSON OUTPUT FORMAT ONLY (no markdown code blocks, no intro text):
{{
  "destination": "{destination}",
  "num_days": {num_days},
  "budget_level": "{budget_level}",
  "estimated_daily_budget": "e.g., ₹1,200 - ₹1,800/day",
  "transit_summary": "1 concise sentence on best local commute mode.",
  "days": [
    {{
      "day_number": 1,
      "theme": "Day theme (e.g. Heritage Forts & Biryani Trails)",
      "morning": {{
        "activity": "Morning Landmark or Routine",
        "description": "Exploration details, timing, or workout/routine specifics.",
        "duration": "3 hrs"
      }},
      "afternoon": {{
        "activity": "Afternoon Spot / Activity",
        "description": "Indoor attraction, gallery, or scenic view.",
        "duration": "2.5 hrs"
      }},
      "evening": {{
        "activity": "Evening Spot / Event / Bazaar Walk",
        "description": "Evening vibe, live event, comedy show, or shopping street.",
        "duration": "3 hrs"
      }},
      "dining_plan": {{
        "breakfast": "Recommended morning breakfast dish & spot type",
        "lunch": "Specific lunch recommendation (signature dish)",
        "dinner": "Signature dinner spot or street food street"
      }},
      "pro_tip": "Practical insider tip for Day 1."
    }}
  ]
}}
"""

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=3800,
            response_mime_type="application/json"
        )

        candidate_models = [
            self.active_model,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]
        candidate_models = list(dict.fromkeys(candidate_models))

        for model in candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Building custom itinerary with food plan ({model}) [Attempt {attempt + 1}]")
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
                        raw_days = parsed.get("days") or []

                        if isinstance(raw_days, list) and len(raw_days) > 0:
                            clean_days = []
                            for idx, d in enumerate(raw_days):
                                clean_days.append({
                                    "day_number": d.get("day_number", idx + 1),
                                    "theme": d.get("theme", f"Day {idx + 1} Exploration"),
                                    "morning": _clean_slot(d.get("morning"), "Morning Sightseeing"),
                                    "afternoon": _clean_slot(d.get("afternoon"), "Afternoon Discovery"),
                                    "evening": _clean_slot(d.get("evening"), "Evening Promenade"),
                                    "dining_plan": _clean_dining(d.get("dining_plan")),
                                    "pro_tip": d.get("pro_tip", "Start early to beat the daytime crowds.")
                                })

                            parsed["days"] = clean_days
                            parsed["destination"] = parsed.get("destination") or destination
                            parsed["num_days"] = parsed.get("num_days") or num_days
                            parsed["budget_level"] = parsed.get("budget_level") or budget_level
                            self.active_model = model
                            return parsed
                except Exception as e:
                    logger.warning(f"Itinerary model {model} failed: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.2)
                        continue
                    break

        fallback_places = selected_places or ["Historic Landmarks", "Local Bazaar", "Cultural Museum"]
        return {
            "destination": destination,
            "num_days": num_days,
            "budget_level": budget_level,
            "estimated_daily_budget": f"{budget_level} allocated across {num_days} days",
            "transit_summary": "Use metro and local autos for comfortable city navigation.",
            "days": [
                {
                    "day_number": i + 1,
                    "theme": f"Exploring {destination} Highlights (Part {i + 1})",
                    "morning": {
                        "activity": fallback_places[i % len(fallback_places)],
                        "description": "Start early to explore before peak heat and avoid crowds.",
                        "duration": "3 hrs"
                    },
                    "afternoon": {
                        "activity": "Cultural Exploration & Galleries",
                        "description": "Explore regional art collections and local craft workshops.",
                        "duration": "2.5 hrs"
                    },
                    "evening": {
                        "activity": "Sunset Point & Night Market",
                        "description": "Stroll the illuminated markets and sample local delicacies.",
                        "duration": "3 hrs"
                    },
                    "dining_plan": {
                        "breakfast": "Traditional local breakfast (e.g. Idli/Dosa or regional tea & snacks)",
                        "lunch": "Signature thali or regional specialty platter",
                        "dinner": "Authentic dinner at an established heritage restaurant"
                    },
                    "pro_tip": "Carry cash for local street food vendors and smaller kiosks."
                }
                for i in range(num_days)
            ]
        }


_itinerary_service = None


def get_itinerary_service() -> ItineraryService:
    global _itinerary_service
    if _itinerary_service is None:
        _itinerary_service = ItineraryService()
    return _itinerary_service