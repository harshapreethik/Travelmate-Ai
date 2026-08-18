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
        return {"activity": slot.strip(), "description": f"Explore {slot.strip()} with local visitor highlights.", "duration": "2.5 hrs"}
    return {"activity": default_activity, "description": f"Explore {default_activity}.", "duration": "2.5 hrs"}


def _clean_dining(dining, destination="Hyderabad"):
    """Ensures breakfast, lunch, and dinner always recommend specific authentic dishes and places."""
    if isinstance(dining, dict):
        return {
            "breakfast": dining.get("breakfast") or f"Traditional breakfast (e.g., Irani Chai & Osmania Biscuits or Dosa)",
            "lunch": dining.get("lunch") or f"Authentic regional lunch (e.g., Dum Biryani or Andhra Meals)",
            "dinner": dining.get("dinner") or f"Popular local dinner or famous street food lane in {destination}"
        }
    elif isinstance(dining, str) and dining.strip():
        return {
            "breakfast": "Traditional morning tiffin & hot coffee/tea",
            "lunch": dining.strip(),
            "dinner": f"Signature evening dinner in {destination}"
        }
    return {
        "breakfast": "Signature local breakfast and morning beverage",
        "lunch": "Authentic regional lunch specialty",
        "dinner": "Signature local dinner at a renowned eatery"
    }


class ItineraryService:
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

    def generate_itinerary(
        self,
        destination: str = "Hyderabad",
        num_days: int = 2,
        budget_level: str = "₹5,000",
        traveller_type: str = "Solo Explorer",
        selected_places: list = None,
        custom_schedule: str = "",
        **kwargs
    ) -> dict:
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
            "You NEVER use generic placeholder phrases like 'Historic Landmarks', 'Cultural Exploration', 'Local Bazaar', 'Sunset Point', "
            "or vague dining descriptions. Every activity must name exact monuments, bazaars, cafes, authentic dishes, and transport modes."
        )

        prompt = f"""
Generate a comprehensive, realistic {num_days}-day travel itinerary for:
- Destination: {destination}
- Duration: {num_days} Days
- Total Budget: {budget_level}
- Traveler Persona: {traveller_type}
{cart_directive}
{custom_directive}

REQUIREMENTS FOR EACH DAY:
1. THEME: A vivid title reflecting the neighborhood or focus of the day.
2. MORNING / AFTERNOON / EVENING: Name the EXACT real-world place (e.g. 'Golconda Fort & Acoustics Walk', 'Nimrah Cafe & Charminar', 'Salar Jung Museum', 'Hussain Sagar & Tank Bund'). Write 2-3 detailed sentences with visitor tips, timings, and photography advice.
3. DINING PLAN:
   - breakfast: Specific dish and authentic place (e.g. 'Ghee Karam Dosa & Filter Coffee at Shankar Vilas / Ram Ki Bandi')
   - lunch: Specific signature meal (e.g. 'Authentic Mutton Dum Biryani at Hotel Shadab or Bawarchi')
   - dinner: Specific spot (e.g. 'Kebabs and Pathar ka Gosht at Bade Miyan / Dine at Jewel of Nizam')
4. PRO TIP: 1 insider tip for ticket booking, queue skips, or transport.

STRICT JSON OUTPUT ONLY (Valid JSON matching this exact structure):
{{
  "destination": "{destination}",
  "num_days": {num_days},
  "budget_level": "{budget_level}",
  "estimated_daily_budget": "₹1,200 - ₹2,000/day",
  "transit_summary": "Use the Metro Red Line and local autos/cabs for hassle-free transit across the city.",
  "days": [
    {{
      "day_number": 1,
      "theme": "Heritage Landmarks, Nizami Architecture & Culinary Icons",
      "morning": {{
        "activity": "Charminar & Laad Bazaar Heritage Walk",
        "description": "Start early at 8:30 AM to explore Charminar's 16th-century architecture before the heat and crowds pick up. Wander the historic pearl and lac bangle shops in Laad Bazaar.",
        "duration": "2.5 hrs"
      }},
      "afternoon": {{
        "activity": "Chowmahalla Palace & Old City Feast",
        "description": "Explore the grand Durbar Hall (Khilwat Mubarak) and vintage car exhibits of the Nizams. Head nearby for an authentic Biryani lunch.",
        "duration": "2.5 hrs"
      }},
      "evening": {{
        "activity": "Golconda Fort & Acoustic Echo Exploration",
        "description": "Climb up to Bala Hissar pavilion for panoramic city views at sunset, followed by the evening sound and light show.",
        "duration": "3 hrs"
      }},
      "dining_plan": {{
        "breakfast": "Irani Chai and fresh Osmania Biscuits at Nimrah Cafe & Bakery",
        "lunch": "Authentic Hyderabadi Dum Biryani with Mirchi ka Salan at Hotel Shadab",
        "dinner": "Pathar ka Gosht and Haleem at Pista House or Shah Ghouse"
      }},
      "pro_tip": "Book ASI monument tickets online at entry gates via QR code to bypass the long manual ticket queues."
    }}
  ]
}}
"""

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
            max_output_tokens=4000,
            response_mime_type="application/json"
        )

        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Generating rich custom itinerary with model ({model}) [Attempt {attempt + 1}]")
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
                                fallback_spot = cleaned_places[idx % len(cleaned_places)] if cleaned_places else f"{destination} Heritage Core"
                                clean_days.append({
                                    "day_number": d.get("day_number", idx + 1),
                                    "theme": d.get("theme", f"Day {idx + 1}: Exploring {fallback_spot}"),
                                    "morning": _clean_slot(d.get("morning"), fallback_spot),
                                    "afternoon": _clean_slot(d.get("afternoon"), f"{destination} Cultural Trail"),
                                    "evening": _clean_slot(d.get("evening"), f"{destination} Evening Promenade"),
                                    "dining_plan": _clean_dining(d.get("dining_plan"), destination),
                                    "pro_tip": d.get("pro_tip", "Pre-book online tickets and keep UPI active for local street stalls.")
                                })

                            parsed["days"] = clean_days
                            parsed["destination"] = parsed.get("destination") or destination
                            parsed["num_days"] = parsed.get("num_days") or num_days
                            parsed["budget_level"] = parsed.get("budget_level") or budget_level
                            self.active_model = model
                            return parsed

                except Exception as e:
                    logger.warning(f"Itinerary model {model} attempt {attempt + 1} failed: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.0)
                        continue
                    break

        # High-Quality Real-Life Guide Fallback (Tailored with concrete spots)
        spots = cleaned_places if cleaned_places else ["Charminar & Old City", "Golconda Fort", "Nimrah Cafe", "Salar Jung Museum", "Hussain Sagar"]
        fallback_days = []
        
        sample_guides = [
            {
                "theme": "Historic Forts, Acoustic Echoes & Old City Delicacies",
                "morning_act": spots[0] if len(spots) > 0 else "Charminar & Laad Bazaar",
                "morning_desc": "Start early around 8:30 AM to explore before peak heat. Walk through the bustling historic lanes of Laad Bazaar.",
                "afternoon_act": spots[1] if len(spots) > 1 else "Chowmahalla Palace & Royal Exhibits",
                "afternoon_desc": "Explore the grand Nizami halls and vintage car collections, followed by an authentic lunch nearby.",
                "evening_act": spots[2] if len(spots) > 2 else "Golconda Fort Sunset View",
                "evening_desc": "Climb up to the royal pavilion for sunset views over the city skyline, followed by the evening light show.",
                "bfast": "Irani Chai and hot Osmania Biscuits at Nimrah Cafe and Bakery",
                "lunch": "Authentic Hyderabadi Mutton Dum Biryani at Hotel Shadab or Bawarchi",
                "dinner": "Pathar ka Gosht and Kebabs at Shah Ghouse / Chicha's",
                "tip": "Scan the official ASI QR code at fort gates for instant online tickets and zero queue time."
            },
            {
                "theme": "Museum Treasures, Lakeside Sunset & Modern Food Streets",
                "morning_act": spots[3] if len(spots) > 3 else "Salar Jung Museum & Jade Gallery",
                "morning_desc": "Explore world-famous artifacts including the Veiled Rebecca and Musical Clock. Arrive at opening time (10 AM).",
                "afternoon_act": spots[4] if len(spots) > 4 else "Qutb Shahi Tombs Heritage Park",
                "afternoon_desc": "Walk through the landscaped gardens and Persian-style domed tombs of the seven Qutb Shahi rulers.",
                "evening_act": "Hussain Sagar Lake, Buddha Statue & Tank Bund Promenade",
                "evening_desc": "Take the ferry boat to the central monolithic Buddha statue, then stroll along the illuminated Tank Bund promenade.",
                "bfast": "Ghee Karam Dosa and Filter Coffee at Minerva Grand / Ram Ki Bandi",
                "lunch": "Royal Andhra Thali with Guntur Gongura pachadi at Kakatiya Deluxe Mess",
                "dinner": "Lakeview rooftop dining or street food trail at Madhapur 100 Feet Road",
                "tip": "Take the Hyderabad Metro to bypass peak evening traffic along the major corridors."
            }
        ]

        for i in range(num_days):
            g = sample_guides[i % len(sample_guides)]
            fallback_days.append({
                "day_number": i + 1,
                "theme": f"Day {i + 1}: {g['theme']}",
                "morning": {
                    "activity": g["morning_act"],
                    "description": g["morning_desc"],
                    "duration": "3 hrs"
                },
                "afternoon": {
                    "activity": g["afternoon_act"],
                    "description": g["afternoon_desc"],
                    "duration": "2.5 hrs"
                },
                "evening": {
                    "activity": g["evening_act"],
                    "description": g["evening_desc"],
                    "duration": "3 hrs"
                },
                "dining_plan": {
                    "breakfast": g["bfast"],
                    "lunch": g["lunch"],
                    "dinner": g["dinner"]
                },
                "pro_tip": g["tip"]
            })

        return {
            "destination": destination,
            "num_days": num_days,
            "budget_level": budget_level,
            "estimated_daily_budget": f"{budget_level} allocated across {num_days} days",
            "transit_summary": "Use metro and local autos for comfortable city travel.",
            "days": fallback_days
        }


_itinerary_service = None


def get_itinerary_service() -> ItineraryService:
    global _itinerary_service
    if _itinerary_service is None:
        _itinerary_service = ItineraryService()
    return _itinerary_service