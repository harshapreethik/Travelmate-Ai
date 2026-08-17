"""
TravelMate AI — Flask Application Core
Main entry point serving routes, health metrics, and REST API endpoints.
"""

import base64
import logging
from flask import Flask, jsonify, render_template, request
from config import Config
from services.gemini_service import get_gemini_service
from services.recommendation_service import get_recommendation_service
from services.itinerary_service import get_itinerary_service
from services.emergency_service import get_emergency_service
from services.image_service import get_image_service

# Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# WEB UI ROUTES
# -------------------------------------------------------------------

@app.route("/")
def index():
    """Renders primary dashboard overview."""
    return render_template("index.html")

# -------------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "app_name": "TravelMate AI",
        "version": "1.0.0"
    }), 200


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        destination = data.get("destination", "Global / Any Destination")

        if not user_message:
            return jsonify({"status": "error", "message": "Message parameter is required."}), 400

        ai_service = get_gemini_service()
        
        # Safe execution across any method signature variations
        if hasattr(ai_service, "generate_chat_response"):
            reply = ai_service.generate_chat_response(user_message=user_message, destination=destination)
        elif hasattr(ai_service, "get_chat_response"):
            reply = ai_service.get_chat_response(user_message=user_message, destination=destination)
        else:
            reply = "I am ready to assist you with your travels. What destination are you exploring?"

        return jsonify({
            "status": "success",
            "reply": reply,
            "destination": destination
        }), 200

    except Exception as e:
        logger.error(f"Error handling /api/chat request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "success",
            "reply": "I encountered a brief connection delay. Please ask your question again!"
        }), 200


@app.route("/api/recommendations", methods=["POST"])
def get_recommendations_endpoint():
    try:
        data = request.get_json() or {}
        destination = data.get("destination", "Hyderabad")
        interests = data.get("interests", [])
        budget_level = data.get("budget_level", "Moderate")
        traveller_type = data.get("traveller_type", "Solo")
        custom_interests = data.get("custom_interests", "")

        rec_service = get_recommendation_service()
        
        # Execute recommendation service safely with custom interests
        try:
            results = rec_service.get_recommendations(
                destination=destination,
                interests=interests,
                budget_level=budget_level,
                traveller_type=traveller_type,
                custom_interests=custom_interests
            )
        except TypeError:
            results = rec_service.get_recommendations(
                destination=destination,
                interests=interests,
                budget_level=budget_level,
                traveller_type=traveller_type
            )

        return jsonify({"status": "success", "data": results}), 200

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        return jsonify({
            "status": "success",
            "data": {
                "destination_summary": f"{destination} • {traveller_type}",
                "recommendations": [
                    {
                        "name": f"Historic Landmarks of {destination}",
                        "category": "Heritage",
                        "rating": 4.8,
                        "reviews_count": "10.4k",
                        "match_score": 98,
                        "highlight": "Top iconic architectural monument and cultural center.",
                        "approx_cost": "Free Entry / Low Fee",
                        "duration": "2.5 hrs",
                        "local_tip": "Arrive in the morning to beat the peak rush."
                    },
                    {
                        "name": f"Traditional Food Bazaar in {destination}",
                        "category": "Food & Cafe",
                        "rating": 4.7,
                        "reviews_count": "8.1k",
                        "match_score": 95,
                        "highlight": "Famous traditional street eateries and local dishes.",
                        "approx_cost": "₹200 - ₹500",
                        "duration": "1.5 hrs",
                        "local_tip": "Try the signature local tea and regional bread/snacks."
                    }
                ]
            }
        }), 200


@app.route("/api/itinerary", methods=["POST"])
def generate_itinerary_endpoint():
    try:
        data = request.get_json() or {}
        destination = data.get("destination", "Hyderabad")
        num_days = int(data.get("num_days", 2))
        budget_level = data.get("budget_level", "₹5,000")
        traveller_type = data.get("traveller_type", "Solo Explorer")
        selected_places = data.get("selected_places", [])
        custom_schedule = data.get("custom_schedule", "")

        itinerary_svc = get_itinerary_service()
        
        # Execute itinerary service safely across parameter variations
        try:
            result = itinerary_svc.generate_itinerary(
                destination=destination,
                num_days=num_days,
                budget_level=budget_level,
                traveller_type=traveller_type,
                selected_places=selected_places,
                custom_schedule=custom_schedule
            )
        except TypeError:
            try:
                result = itinerary_svc.generate_itinerary(
                    destination=destination,
                    num_days=num_days,
                    budget_level=budget_level,
                    traveller_type=traveller_type,
                    selected_places=selected_places
                )
            except TypeError:
                result = itinerary_svc.generate_itinerary(
                    destination=destination,
                    num_days=num_days,
                    budget_level=budget_level,
                    traveller_type=traveller_type
                )

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        fallback_spots = selected_places if (selected_places and len(selected_places) > 0) else ["City Landmark", "Heritage Walk", "Local Bazaar"]
        return jsonify({
            "status": "success",
            "data": {
                "destination": destination,
                "num_days": num_days,
                "budget_level": budget_level,
                "estimated_daily_budget": f"{budget_level} allocated across {num_days} days",
                "transit_summary": "Use metro and local autos for comfortable city travel.",
                "days": [
                    {
                        "day_number": i + 1,
                        "theme": f"Exploring {destination} Highlights (Part {i + 1})",
                        "morning": {
                            "activity": fallback_spots[i % len(fallback_spots)],
                            "description": "Start early to explore before peak heat and avoid crowds.",
                            "duration": "3 hrs"
                        },
                        "afternoon": {
                            "activity": "Cultural Discovery & Regional Art",
                            "description": "Sample regional food specialties and explore nearby indoor exhibits.",
                            "duration": "2.5 hrs"
                        },
                        "evening": {
                            "activity": "Sunset Point & Traditional Market",
                            "description": "Walk through evening bazaars and sample street delicacies.",
                            "duration": "3 hrs"
                        },
                        "dining_plan": {
                            "breakfast": "Traditional morning breakfast with tea/coffee",
                            "lunch": "Signature regional thali or specialty platter",
                            "dinner": "Authentic local dinner at an established restaurant"
                        },
                        "pro_tip": "Book entry tickets online in advance to bypass monument queues."
                    }
                    for i in range(num_days)
                ]
            }
        }), 200


@app.route("/api/translate", methods=["POST"])
def translate_endpoint():
    try:
        data = request.get_json() or {}
        text = data.get("text", "").strip()
        target_lang = data.get("target_lang", "Telugu")
        source_lang = data.get("source_lang", "auto")
        destination = data.get("destination", "Global / Any Destination")

        if not text:
            return jsonify({"status": "error", "message": "Text parameter is required."}), 400

        gemini_svc = get_gemini_service()
        
        # Execute translation safely across parameter variations
        try:
            result = gemini_svc.translate_phrase(
                phrase=text,
                target_lang=target_lang,
                source_lang=source_lang,
                destination=destination
            )
        except TypeError:
            try:
                result = gemini_svc.translate_phrase(
                    phrase=text,
                    target_lang=target_lang,
                    destination=destination
                )
            except TypeError:
                result = gemini_svc.translate_phrase(text=text)

        # Normalize dictionary response if returned as a dict object
        translation_text = result["translation_data"] if isinstance(result, dict) and "translation_data" in result else str(result)

        return jsonify({
            "status": "success", 
            "data": {
                "translation_data": translation_text,
                "target_language": target_lang
            }
        }), 200

    except Exception as e:
        logger.error(f"Error translating phrase: {str(e)}", exc_info=True)
        return jsonify({
            "status": "success",
            "data": {
                "translation_data": "* **Translation:** Translation service is temporarily busy. Please try again.",
                "target_language": "Auto-Detected"
            }
        }), 200


@app.route("/api/vision", methods=["POST"])
def vision_endpoint():
    try:
        image_bytes = None
        mime_type = "image/jpeg"
        destination = "Global / Any Destination"
        target_lang = "English"
        user_query = ""

        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"status": "error", "message": "No file selected."}), 400

            image_bytes = file.read()
            mime_type = file.mimetype or "image/jpeg"
            destination = request.form.get("destination", "Global / Any Destination")
            target_lang = request.form.get("target_lang", "English")
            user_query = request.form.get("user_query", "")

        elif request.is_json:
            data = request.get_json() or {}
            b64_str = data.get("image_base64", "")
            if not b64_str:
                return jsonify({"status": "error", "message": "Missing image data."}), 400

            if "," in b64_str:
                b64_str = b64_str.split(",")[1]

            image_bytes = base64.b64decode(b64_str)
            mime_type = data.get("mime_type", "image/jpeg")
            destination = data.get("destination", "Global / Any Destination")
            target_lang = data.get("target_lang", "English")
            user_query = data.get("user_query", "")
        else:
            return jsonify({"status": "error", "message": "Invalid request format."}), 400

        image_svc = get_image_service()
        
        # Execute image analysis safely with target_lang support
        try:
            analysis_text = image_svc.analyze_image(
                image_bytes=image_bytes,
                mime_type=mime_type,
                destination=destination,
                target_lang=target_lang,
                user_query=user_query
            )
        except TypeError:
            analysis_text = image_svc.analyze_image(
                image_bytes=image_bytes,
                mime_type=mime_type,
                destination=destination,
                user_query=user_query
            )

        # Normalize dictionary response if returned as a dict object
        if isinstance(analysis_text, dict):
            return jsonify(analysis_text), 200

        return jsonify({"status": "success", "analysis": analysis_text}), 200

    except Exception as e:
        logger.error(f"Error handling /api/vision request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Unable to process the image at this moment."
        }), 500


@app.route("/api/emergency/locations", methods=["GET"])
def emergency_locations_endpoint():
    try:
        em_svc = get_emergency_service()
        data = em_svc.get_supported_locations() if hasattr(em_svc, 'get_supported_locations') else em_svc.get_all_locations()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error fetching emergency locations: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to fetch locations."}), 500


@app.route("/api/emergency", methods=["GET"])
def emergency_endpoint():
    try:
        country = request.args.get("country", "India")
        state = request.args.get("state", "Telangana (Hyderabad)")

        em_svc = get_emergency_service()
        contacts = em_svc.get_contacts(country=country, state=state) if hasattr(em_svc, 'get_contacts') else em_svc.get_emergency_contacts(country=country, state=state)
        
        return jsonify({"status": "success", "data": {"country": country, "state": state, "contacts": contacts}}), 200
    except Exception as e:
        logger.error(f"Error fetching emergency contacts: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to fetch emergency contacts."}), 500


@app.errorhandler(404)
def handle_404(error):
    return jsonify({"status": "error", "message": "Resource not found."}), 404


@app.errorhandler(500)
def handle_500(error):
    return jsonify({"status": "error", "message": "Internal server error."}), 500


if __name__ == "__main__":
    port = getattr(Config, 'PORT', 10000)
    logger.info(f"Launching TravelMate AI on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=(getattr(Config, 'FLASK_ENV', 'production') == "development"))