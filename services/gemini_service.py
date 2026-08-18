"""
TravelMate AI — Unified Gemini & Intelligence Services
All-in-one production engine supporting:
1. Universal Conversational AI & Multilingual Assistant (auto language/script detection & natural dialogue)
2. Places & Venue Recommendation Engine (with budget tiers & custom preferences)
3. Smart Itinerary Planner (with Trip Cart sync & daily meal/dining logistics)
4. Vision OCR & Visual Analysis
5. Travel Translator & Cultural Etiquette Guide
"""

import json
import logging
import re
import time
from google import genai
from google.genai import types
from config import Config

logger = logging.getLogger(__name__)


class TravelMateService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.active_model = getattr(Config, "GEMINI_MODEL", "gemini-2.5-flash")
        self.candidate_models = [
            getattr(Config, "GEMINI_MODEL", "gemini-2.5-flash"),
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]

    # =========================================================================
    # SECTION 1: DETAILED & NATURAL CONVERSATIONAL ASSISTANT
    # =========================================================================
    def generate_chat_response(
        self,
        user_message: str,
        chat_history: list = None,
        destination: str = "Global / Any Destination"
    ) -> str:
        """
        Converses naturally like an experienced local friend via live Gemini API.
        Provides comprehensive, high-value responses with full day logistics,
        routes, timings, and authentic food joints with Google Maps search links.
        """
        system_instruction = (
            "You are TravelMate AI, an expert, authentic, and culturally knowledgeable local travel companion. "
            "You talk like a helpful local peer who knows every hidden gem, bus number, timing, and food spot.\n\n"
            "CRITICAL CONVERSATIONAL GUIDELINES:\n"
            "1. THOROUGH & ACTIONABLE DETAIL:\n"
            "   - Do NOT give 2-sentence superficial answers. Provide detailed, practical guidance with specific morning, afternoon, and evening timelines when asked for a plan.\n"
            "   - When multi-location trips or routes are asked (e.g., Hyderabad to Amaravathi/Guntur), break down: (a) Starting point & transit routes, (b) Exact food/tiffin recommendations, (c) Bus station name, highway route, travel duration, and fare, (d) Sightseeing spots in chronological order.\n"
            "2. LANGUAGE & SCRIPT MIRRORING:\n"
            "   - If the user types in Transliterated English (e.g., Tanglish: 'hyderabad nunchi amt ki vellali locatioon route ivu', Hinglish, Tamglish), "
            "     you MUST respond completely in that EXACT SAME natural transliterated conversational language (Tanglish with English letters).\n"
            "   - If the user types in native Telugu (తెలుగు), reply in pure Telugu script.\n"
            "   - If the user types in English, reply in polished conversational English.\n"
            "3. REAL-WORLD NAMES & DIRECT GOOGLE MAPS LINKS (CRITICAL):\n"
            "   - Always name exact temples, statues, forts, bakeries, tiffin centers, bus stands, and restaurants.\n"
            "   - Whenever you mention a specific place, landmark, or eatery, embed a clickable Google Maps Markdown link using this exact format:\n"
            "     [Place Name](https://www.google.com/maps/search/?api=1&query=URL_ENCODED_PLACE_NAME+CITY)\n"
            "     Examples:\n"
            "     * [Dhyana Buddha Statue](https://www.google.com/maps/search/?api=1&query=Dhyana+Buddha+Statue+Amaravathi)\n"
            "     * [MGBS Hyderabad](https://www.google.com/maps/search/?api=1&query=Mahatma+Gandhi+Bus+Station+Hyderabad)\n"
            "     * [Amareswara Swamy Temple](https://www.google.com/maps/search/?api=1&query=Amareswara+Swamy+Temple+Amaravathi)"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=3000
        )

        last_error = None
        for model in self.candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=user_message,
                    config=config
                )
                if response and response.text:
                    self.active_model = model
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Chat model {model} failed: {e}")
                last_error = e
                continue

        # Surface exact API exception instead of silent hardcoded default
        return f"Unable to reach the AI model ({last_error}). Please check your GEMINI_API_KEY and network connection."

    # =========================================================================
    # SECTION 2: PLACES & SPOT RECOMMENDATION ENGINE
    # =========================================================================
    def get_recommendations(
        self,
        destination: str,
        interests: list = None,
        budget_level: str = "Moderate",
        traveller_type: str = "Solo",
        custom_interests: str = ""
    ) -> dict:
        combined_interests = ", ".join(interests) if interests else "Heritage, Food, Nature"
        if custom_interests:
            combined_interests += f" | Custom Routine/Preferences: {custom_interests}"

        prompt = f"""
You are a live travel directory database engine.
Generate exactly 4 to 6 top spot recommendations for:
- City/Destination: {destination}
- Traveler Persona: {traveller_type}
- Budget Tier / Max Cost: {budget_level}
- Categories & Custom Interests: {combined_interests}

STRICT JSON OUTPUT FORMAT ONLY (No markdown formatting tags, no intro text):
{{
  "destination_summary": "{destination} • {traveller_type}",
  "recommendations": [
    {{
      "name": "Exact Real-World Name of Place or Restaurant",
      "category": "Heritage / Food & Cafe / Nature / Fitness / Event / Shopping",
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
            temperature=0.2,
            max_output_tokens=2500,
            response_mime_type="application/json"
        )

        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Fetching recommendations via ({model}) [Attempt {attempt + 1}]")
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
                            return parsed
                except Exception as e:
                    logger.warning(f"Recommendation model {model} failed: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.2)
                        continue
                    break

        return {
            "destination_summary": f"{destination} • {traveller_type}",
            "recommendations": []
        }

    # =========================================================================
    # SECTION 3: ITINERARY PLANNER
    # =========================================================================
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
            extra_prompts.append(f"- USER SELECTED ATTRACTIONS (MUST INCLUDE & DISTRIBUTE): {places_list_str}")
        if custom_schedule:
            extra_prompts.append(f"- USER CUSTOM ROUTINES & EVENTS TO INTEGRATE: {custom_schedule}")

        extras_str = "\n".join(extra_prompts)

        prompt = f"""
You are an expert travel logistics architect and culinary planner.
Generate a structured day-by-day itinerary with full dining plans for:
- Destination: {destination}
- Duration: {num_days} Days
- Budget: {budget_level}
- Traveler Persona: {traveller_type}
{extras_str}

STRICT JSON OUTPUT FORMAT ONLY:
{{
  "destination": "{destination}",
  "num_days": {num_days},
  "budget_level": "{budget_level}",
  "estimated_daily_budget": "e.g., ₹1,200 - ₹1,800/day",
  "transit_summary": "1 concise sentence on best commute mode.",
  "days": [
    {{
      "day_number": 1,
      "theme": "Day theme (e.g. Heritage Forts & Biryani Trails)",
      "morning": {{
        "activity": "Exact Landmark or Routine",
        "description": "Exploration details, timing, or workout specifics.",
        "duration": "3 hrs"
      }},
      "afternoon": {{
        "activity": "Afternoon Spot / Activity",
        "description": "Indoor attraction, gallery, or scenic viewpoint.",
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

        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Building custom itinerary with ({model}) [Attempt {attempt + 1}]")
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
                        if "days" in parsed and len(parsed["days"]) > 0:
                            self.active_model = model
                            return parsed
                except Exception as e:
                    logger.warning(f"Itinerary model {model} failed: {e}")
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        time.sleep(1.2)
                        continue
                    break

        return {
            "destination": destination,
            "num_days": num_days,
            "budget_level": budget_level,
            "estimated_daily_budget": f"{budget_level} allocated across {num_days} days",
            "transit_summary": "Use metro and local autos for comfortable navigation.",
            "days": []
        }

    # =========================================================================
    # SECTION 4: VISION / MENU & SIGNBOARD OCR
    # =========================================================================
    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        destination: str = "Global",
        user_query: str = ""
    ) -> str:
        prompt = (
            f"You are TravelMate AI's visual intelligence engine.\n"
            f"Context Destination: {destination}\n"
            f"User Instructions: {user_query if user_query else 'Analyze this image in detail for a traveler.'}\n\n"
            "TASK:\n"
            "1. Transcribe all readable text on signs, menus, boards, or monuments.\n"
            "2. If it is a menu, identify signature dishes, vegetarian/non-vegetarian items, dietary notes, and estimated pricing.\n"
            "3. If it is a landmark/signboard, explain its historical significance and practical visitor advice.\n"
            "4. Format the output cleanly in Markdown with bold titles and bullet points."
        )

        for model in self.candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt
                    ]
                )
                if response and response.text:
                    self.active_model = model
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Vision analysis failed on {model}: {e}")
                continue

        return "Unable to analyze the image at this moment. Please check the image resolution and try again."

    # =========================================================================
    # SECTION 5: TRANSLATOR & ETIQUETTE GUIDE
    # =========================================================================
    def translate_phrase(
        self,
        phrase: str,
        target_lang: str = "auto",
        destination: str = "Global / Any Destination"
    ) -> str:
        prompt = (
            f"You are TravelMate AI's universal smart travel translator.\n"
            f"Context / Destination: {destination}\n\n"
            f"Input Phrase: \"{phrase}\"\n\n"
            "TASK:\n"
            f"1. Detect the input language and user intent.\n"
            f"2. Translate into '{target_lang}' if specified, or the primary local language of {destination} if 'auto'.\n"
            "3. Return output strictly formatted in Markdown:\n"
            "* **Detected Input:** [Language and Script]\n"
            "* **Translation:** [Translated text in native script]\n"
            "* **Phonetic Pronunciation:** [Pronunciation in Latin/English letters]\n"
            "* **Traveler Note / Etiquette:** [1 short practical tip]"
        )

        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=600
        )

        for model in self.candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                if response and response.text:
                    self.active_model = model
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Translation failed on {model}: {e}")
                continue

        return "* **Translation:** Translation service is temporarily busy. Please try again."


# Singleton Instance Provider
_service_instance = None


def get_travelmate_service() -> TravelMateService:
    global _service_instance
    if _service_instance is None:
        _service_instance = TravelMateService()
    return _service_instance


# Backward-compatible aliases for legacy imports
get_gemini_service = get_travelmate_service
get_recommendation_service = get_travelmate_service
get_itinerary_service = get_travelmate_service