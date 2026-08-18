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


# services/gemini_service.py
class TravelMateService:
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
        Maintains conversational history within the active browser session.
        """
        system_instruction = (
            "You are TravelMate AI, an expert, authentic, and practical global travel companion.\n\n"
            "STRICT CONVERSATION & TOPIC CONTINUITY RULE:\n"
            "- Always maintain conversational context from prior messages. If the user asks a follow-up "
            "(e.g., '3 to 4 days lo plan cheyachu ga' or 'what about food there?'), apply that constraint directly "
            "to the active destination under discussion rather than jumping to unrelated locations.\n\n"
            "STRICT LANGUAGE MATCHING PROTOCOL:\n"
            "- If the user writes in standard English, respond 100% in pure English.\n"
            "- If the user writes in Telugu script (తెలుగు), respond in Telugu script.\n"
            "- If the user writes in transliterated Telugu / Tanglish (e.g., 'ela unnav', 'route cheppu'), respond in natural conversational Tanglish.\n"
            "- If the user writes in Hindi / Hinglish, respond in Hindi / Hinglish.\n"
            "- NEVER use regional slang or Telugu transliteration unless the user's latest message explicitly used it.\n\n"
            "RESPONSE RULES & GOOGLE MAPS INTEGRATION:\n"
            "1. Thorough & Actionable Detail: Provide structured morning, afternoon, and evening timelines with transit tips, realistic timings, and exact food recommendations.\n"
            "2. Exact Real-World Names: Always name real landmarks, restaurants, cafes, stations, and dishes.\n"
            "3. Clickable Google Maps Links: Every time you mention a specific attraction, restaurant, or transit hub, format it as a markdown link:\n"
            "   [Place Name](https://www.google.com/maps/search/?api=1&query=URL_ENCODED_PLACE_NAME+CITY)\n"
            "   Example: [Eiffel Tower](https://www.google.com/maps/search/?api=1&query=Eiffel+Tower+Paris)"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=3000
        )

        # Build full multi-turn conversational payload
        contents = []
        if chat_history and isinstance(chat_history, list):
            for msg in chat_history:
                role = "user" if msg.get("role") in ["user", "human"] else "model"
                text = msg.get("text") or (msg.get("parts", [{}])[0].get("text", ""))
                if text:
                    contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        last_error = None
        for model in self.candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                if response and response.text:
                    self.active_model = model
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Chat model {model} failed: {e}")
                last_error = e
                if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    time.sleep(1.0)
                    continue
                continue

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
                    if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
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
                    if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
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
        target_lang: str = "English",
        user_query: str = ""
    ) -> str:
        safe_mime = mime_type.strip() if (mime_type and mime_type.startswith("image/")) else "image/jpeg"
        if "webp" in safe_mime:
            safe_mime = "image/webp"

        prompt = f"""
You are TravelMate AI's visual intelligence and OCR engine.
Context Destination: {destination}
Target Language for Output: {target_lang}
User Instructions: {user_query if user_query else 'Extract, transcribe, and translate all text, signs, dishes, and categories.'}

TASK:
1. Transcribe all readable text from the image.
2. Translate extracted text accurately into {target_lang}.
3. If this is a hazard/signboard, provide a prominent bold hazard explanation and safety advice.
4. If this is a menu, categorize items into Vegetarian (🟢) and Non-Vegetarian (🔴) with pricing notes.
5. Format the output cleanly in Markdown with bold titles and bullet points.
"""

        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=safe_mime)
        except Exception as err:
            logger.error(f"Failed to create image Part: {err}")
            return f"* **Error:** Could not process image ({err})."

        # Vision requires multimodal models (filtering out text-only models)
        vision_models = ["gemini-2.5-flash", "gemini-2.0-flash"]

        for model in vision_models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[image_part, prompt]
                )
                if response and response.text:
                    self.active_model = model
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Vision analysis failed on {model}: {e}")
                if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    time.sleep(1.0)
                    continue
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
                if any(code in str(e) for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    time.sleep(0.8)
                    continue
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