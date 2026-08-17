"""
TravelMate AI — Unified Gemini & Intelligence Services
All-in-one production engine supporting:
1. ChatGPT-like Zero-Config Multilingual Assistant (auto language/script detection & mirroring)
2. Places & Venue Recommendation Engine (with budget sliders & custom interests)
3. Smart Itinerary Planner (with Trip Cart sync & daily meal/food plans)
4. Vision OCR & Visual Analysis
5. Travel Translator & Etiquette Guide
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
        self.active_model = "gemini-2.5-flash"
        self.candidate_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-flash-latest"
        ]

    # =========================================================================
    # SECTION 1: CHATGPT-LIKE UNIVERSAL MULTILINGUAL CHAT ASSISTANT
    # =========================================================================
    def generate_chat_response(
        self,
        user_message: str,
        chat_history: list = None,
        destination: str = "Global / Any Destination"
    ) -> str:
        """
        Behaves like a true AI chat assistant.
        Automatically detects ANY input language, script, dialect, or transliteration
        (e.g., Telugu, Tanglish, Hindi, Hinglish, Tamil, Spanish, French, Japanese, etc.)
        and responds back in that EXACT language, script, and natural conversational tone.
        """
        system_instruction = (
            "You are TravelMate AI, an expert, authentic, and culturally savvy real-time multilingual travel companion.\n\n"
            "CORE INTELLIGENCE & LANGUAGE RULES:\n"
            "1. UNIVERSAL AUTO-DETECTION: You can understand and process EVERY human language, dialect, and script worldwide.\n"
            "2. SCRIPT & TRANSLITERATION MIRRORING (CRITICAL):\n"
            "   - If the user writes in Transliterated English script (e.g. Tanglish: 'hyd lo best spots cheppu', Hinglish: 'delhi me ghumne ki jagah batao', Tamglish, etc.), "
            "     you MUST respond back in that EXACT SAME natural transliterated conversational dialect.\n"
            "   - If the user writes in native script (e.g., తెలుగు, हिन्दी, தமிழ், 日本語, Español), respond in that exact native script.\n"
            "   - If the user writes in English, respond in polished English.\n"
            "3. RESPONSE QUALITY: Be direct, authentic, concise, and helpful. Provide specific place names, local food recommendations, timing tips, and cost estimates.\n"
            "4. CLEAN FORMATTING: Use Markdown bullets and bold highlights for effortless scannability. Do NOT start with meta-announcements or generic fluff."
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
            max_output_tokens=2048
        )

        for model in self.candidate_models:
            for attempt in range(2):
                try:
                    logger.info(f"Chat request with model ({model}) [Attempt {attempt + 1}]")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=user_message,
                        config=config
                    )
                    if response and response.text:
                        self.active_model = model
                        return response.text.strip()
                except Exception as e:
                    err = str(e)
                    logger.warning(f"Chat model {model} attempt {attempt + 1} failed: {err}")
                    if "503" in err or "UNAVAILABLE" in err:
                        time.sleep(1.2)
                        continue
                    break

        return (
            "Here are top highlights to explore:\n\n"
            "* **Historic Core Landmarks:** Visit premier heritage spots in the early morning to beat the crowd.\n"
            "* **Signature Culinary Trails:** Sample authentic regional specialties at established local eateries.\n"
            "* **Evening Promenades & Bazaars:** Stroll traditional night markets for street food, crafts, and sunset views."
        )

    # Alias to prevent method naming mismatches across different routes
    def get_chat_response(self, user_message: str, chat_history: list = None, destination: str = "Global") -> str:
        return self.generate_chat_response(user_message=user_message, chat_history=chat_history, destination=destination)

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
        """
        Curates standalone spots with ratings, costs, and match scores.
        Takes into account custom preferences like workouts, comedy gigs, live events, or late night cafes.
        """
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
      "name": "Exact Name of Place or Restaurant",
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
            "recommendations": [
                {
                    "name": f"Historic Core of {destination}",
                    "category": "Heritage",
                    "rating": 4.8,
                    "reviews_count": "10.5k",
                    "match_score": 98,
                    "highlight": "Top iconic architectural monument and cultural landmark.",
                    "best_time": "9:00 AM - 12:00 PM",
                    "approx_cost": "Free / Low Entry",
                    "duration": "2.5 hrs",
                    "local_tip": "Arrive early morning to skip long ticket counter lines."
                },
                {
                    "name": f"Authentic Culinary Bazaar in {destination}",
                    "category": "Food & Cafe",
                    "rating": 4.7,
                    "reviews_count": "8.2k",
                    "match_score": 95,
                    "highlight": "Famous traditional street eateries and signature local dishes.",
                    "best_time": "1:00 PM - 3:30 PM",
                    "approx_cost": "₹200 - ₹500",
                    "duration": "1.5 hrs",
                    "local_tip": "Try the signature house special dish with local bread/tea."
                }
            ]
        }

    # =========================================================================
    # SECTION 3: ITINERARY PLANNER (WITH TRIP CART & DAILY FOOD PLANS)
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
        """
        Constructs a scheduled day-by-day itinerary incorporating:
        - Priority spots chosen by the user in Section 2 (Trip Cart)
        - Custom schedules (e.g. 7 AM gym, 9 PM standup comedy)
        - Explicit daily dining plans (Breakfast, Lunch, Dinner)
        """
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
        "activity": "Morning Landmark or Routine",
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

        # Fallback schedule preserving cart spots
        fallback_places = selected_places if (selected_places and len(selected_places) > 0) else ["City Landmark", "Heritage Walk", "Local Bazaar"]
        return {
            "destination": destination,
            "num_days": num_days,
            "budget_level": budget_level,
            "estimated_daily_budget": f"{budget_level} allocated across {num_days} days",
            "transit_summary": "Use metro and local autos for comfortable navigation.",
            "days": [
                {
                    "day_number": i + 1,
                    "theme": f"Exploring {destination} Highlights (Part {i + 1})",
                    "morning": {
                        "activity": fallback_places[i % len(fallback_places)],
                        "description": "Start early to explore before peak heat and avoid long queues.",
                        "duration": "3 hrs"
                    },
                    "afternoon": {
                        "activity": "Cultural Exploration & Museum Tour",
                        "description": "Explore regional art collections and local craft workshops.",
                        "duration": "2.5 hrs"
                    },
                    "evening": {
                        "activity": "Sunset Point & Night Market",
                        "description": "Stroll the illuminated markets and sample local delicacies.",
                        "duration": "3 hrs"
                    },
                    "dining_plan": {
                        "breakfast": "Traditional local breakfast (e.g. Idli/Dosa, Chai & bakery snack)",
                        "lunch": "Signature regional thali or local specialty platter",
                        "dinner": "Authentic dinner at an established heritage restaurant"
                    },
                    "pro_tip": "Pre-book online tickets where possible to skip entry lines."
                }
                for i in range(num_days)
            ]
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
            f"TASK:\n"
            f"1. Detect the input language and user intent.\n"
            f"2. Translate into '{target_lang}' if specified, or the primary local language of {destination} if 'auto'.\n"
            f"3. Return output strictly formatted in Markdown:\n"
            f"* **Detected Input:** [Language and Script]\n"
            f"* **Translation:** [Translated text in native script]\n"
            f"* **Phonetic Pronunciation:** [Pronunciation in Latin/English letters]\n"
            f"* **Traveler Note / Etiquette:** [1 short practical tip]"
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