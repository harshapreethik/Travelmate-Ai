"""
TravelMate AI — Itinerary Planning Service
Generates detailed, real-world day-by-day itineraries with authentic dining plans and seamless cart integration.
"""

import json
import logging
import re
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


def _sanitize_places(selected_places):
    """Safely extracts spot names whether passed as strings or dicts from the frontend."""
    cleaned = []
    if selected_places and isinstance(selected_places, list):
        for p in selected_places:
            if isinstance(p, dict):
                name = p.get("name") or p.get("title") or ""
                if name:
                    cleaned.append(name.strip())
            elif isinstance(p, str) and p.strip():
                cleaned.append(p.strip())
    return cleaned


def _clean_slot(slot, default_activity="Local Sightseeing"):
    """Ensures morning/afternoon/evening slots always contain rich activity, description, and duration."""
    if isinstance(slot, dict):
        act = slot.get("activity") or slot.get("name") or default_activity
        desc = slot.get("description") or slot.get("details") or f"Explore {act} with optimal timing to avoid peak rush."
        dur = slot.get("duration") or "2.5 hrs"
        return {"activity": act, "description": desc, "duration": dur}
    elif isinstance(slot, str) and slot.strip():
        return {
            "activity": slot.strip(),
            "description": f"Explore {slot.strip()} with local visitor highlights.",
            "duration": "2.5 hrs"
        }
    return {"activity": default_activity, "description": f"Explore {default_activity}.", "duration": "2.5 hrs"}


def _clean_dining(dining, destination="Destination"):
    """Ensures breakfast, lunch, and dinner always recommend specific authentic dishes and places."""
    if isinstance(dining, dict):
        return {
            "breakfast": dining.get("breakfast") or f"Traditional breakfast and local coffee/tea in {destination}",
            "lunch": dining.get("lunch") or f"Authentic regional lunch specialty in {destination}",
            "dinner": dining.get("dinner") or f"Popular local dinner or famous food street in {destination}"
        }
    elif isinstance(dining, str) and dining.strip():
        return {
            "breakfast": f"Traditional morning breakfast in {destination}",
            "lunch": dining.strip(),
            "dinner": f"Signature evening dinner in {destination}"
        }
    return {
        "breakfast": f"Signature local breakfast in {destination}",
        "lunch": f"Authentic regional lunch specialty in {destination}",
        "dinner": f"Signature local dinner in {destination}"
    }


class ItineraryService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash"
        ]
        self.active_model = self.candidate_models[0]

    def generate_itinerary(
        self,
        destination: str = "Destination",
        num_days: int = 2,
        budget_level: str = "₹5,000",
        traveller_type: str = "Solo Explorer",
        selected_places: list = None,
        custom_schedule: str = "",
        **kwargs
    ) -> dict:
        dest_clean = destination.strip() if destination and destination.strip() else "Global"
        cleaned_places = _sanitize_places(selected_places)
        
        cart_directive = ""
        if cleaned_places:
            cart_spots_str = ", ".join(cleaned_places)
            cart_directive = (
                f"\nCRITICAL USER SELECTIONS (FROM TRIP CART):\n"
                f"The user selected these spots: {cart_spots_str}.\n"
                f"You MUST distribute and incorporate these exact locations into the morning, afternoon, or evening activities across the {num_days} days."
            )

        custom_directive = f"\nUser Custom Routine/Events to Integrate: {custom_schedule}" if custom_schedule else ""

        system_instruction = (
            "You are TravelMate AI, an expert, authentic, and culturally knowledgeable local travel guide and logistics architect. "
            "You provide real-world, highly specific, practical travel itineraries that read like an experienced local friend is guiding you. "
            "You NEVER use generic placeholder phrases like 'Historic Landmarks', 'Cultural Exploration', 'Local Bazaar', or 'Sunset Point'. "
            "Every activity must name exact real-world monuments, bazaars, cafes, authentic regional dishes, and transit modes."
        )

        prompt = f"""
Generate a comprehensive, realistic {num_days}-day travel itinerary for:
- Destination: {dest_clean}
- Duration: {num_days} Days
- Total Budget: {budget_level}
- Traveler Persona: {traveller_type}
{cart_directive}
{custom_directive}

REQUIREMENTS FOR EACH DAY:
1. THEME: A vivid title reflecting the neighborhood or focus of the day.
2. MORNING / AFTERNOON / EVENING: Name the EXACT real-world place in {dest_clean}. Write 2-3 detailed sentences with visitor tips, timings, and photography advice.
3. DINING PLAN:
   - breakfast: Specific dish and authentic place in {dest_clean}
   - lunch: Specific signature meal in {dest_clean}
   - dinner: Specific spot or night market in {dest_clean}
4. PRO TIP: 1 insider tip for ticket booking, queue skips, or transport in {dest_clean}.

STRICT JSON OUTPUT ONLY (Valid JSON matching this exact structure):
{{
  "destination": "{dest_clean}",
  "num_days": {num_days},
  "budget_level": "{budget_level}",
  "estimated_daily_budget": "e.g., ₹1,200 - ₹2,000/day",
  "transit_summary": "1 practical sentence on best transit (metro, local cabs, walking) for {dest_clean}.",
  "days": [
    {{
      "day_number": 1,
      "theme": "Theme of Day 1",
      "morning": {{
        "activity": "Exact Real Place Name",
        "description": "2-3 detailed sentences with visitor tips and route details.",
        "duration": "2.5 hrs"
      }},
      "afternoon": {{
        "activity": "Exact Real Place Name",
        "description": "2-3 detailed sentences with visitor tips.",
        "duration": "2.5 hrs"
      }},
      "evening": {{
        "activity": "Exact Real Place Name",
        "description": "2-3 detailed sentences with evening atmosphere.",
        "duration": "3 hrs"
      }},
      "dining_plan": {{
        "breakfast": "Authentic dish and local cafe",
        "lunch": "Specific lunch specialty",
        "dinner": "Signature dinner spot or street food lane"
      }},
      "pro_tip": "Practical insider tip for Day 1."
    }}
  ]
}}
"""

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.6,
            max_output_tokens=4000,
            response_mime_type="application/json"
        )

        last_error = None
        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Generating rich custom itinerary for '{dest_clean}' with model ({model}) [Attempt {attempt + 1}]")
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
                                fallback_spot = cleaned_places[idx % len(cleaned_places)] if cleaned_places else f"{dest_clean} Landmark"
                                clean_days.append({
                                    "day_number": d.get("day_number", idx + 1),
                                    "theme": d.get("theme", f"Day {idx + 1}: Exploring {dest_clean}"),
                                    "morning": _clean_slot(d.get("morning"), fallback_spot),
                                    "afternoon": _clean_slot(d.get("afternoon"), f"{dest_clean} Sightseeing"),
                                    "evening": _clean_slot(d.get("evening"), f"{dest_clean} Evening Walk"),
                                    "dining_plan": _clean_dining(d.get("dining_plan"), dest_clean),
                                    "pro_tip": d.get("pro_tip", "Pre-book online tickets to bypass queues.")
                                })

                            parsed["days"] = clean_days
                            parsed["destination"] = parsed.get("destination") or dest_clean
                            parsed["num_days"] = parsed.get("num_days") or num_days
                            parsed["budget_level"] = parsed.get("budget_level") or budget_level
                            self.active_model = model
                            logger.info(f"Successfully generated {len(clean_days)}-day itinerary with {model}")
                            return parsed

                except Exception as e:
                    logger.warning(f"Itinerary model {model} attempt {attempt + 1} failed: {e}")
                    last_error = e
                    if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                        time.sleep(1.0)
                        continue
                    break

        logger.error(f"All itinerary models failed for '{dest_clean}'. Last error: {last_error}")
        return {
            "destination": dest_clean,
            "num_days": num_days,
            "budget_level": budget_level,
            "estimated_daily_budget": f"{budget_level} allocated across {num_days} days",
            "transit_summary": "Use local metro and cab services for hassle-free navigation.",
            "days": []
        }


_itinerary_service = None


def get_itinerary_service() -> ItineraryService:
    global _itinerary_service
    if _itinerary_service is None:
        _itinerary_service = ItineraryService()
    return _itinerary_service