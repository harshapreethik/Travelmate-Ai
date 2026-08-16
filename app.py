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
from services.translation_service import get_translation_service
from services.emergency_service import get_emergency_service
from services.image_service import get_image_service

# Initialize Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Validate environment readiness on boot
Config.validate_config()

# -------------------------------------------------------------------
# WEB UI ROUTES
# -------------------------------------------------------------------

@app.route("/")
def index():
    """Renders primary dashboard overview."""
    return render_template("index.html", languages=Config.SUPPORTED_LANGUAGES)

# -------------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "app_name": "TravelMate AI",
        "version": "1.0.0",
        "supported_languages": Config.SUPPORTED_LANGUAGES
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
        reply = ai_service.generate_chat_response(
            user_message=user_message,
            destination=destination
        )

        return jsonify({
            "status": "success",
            "reply": reply,
            "destination": destination
        }), 200

    except Exception as e:
        logger.error(f"Error handling /api/chat request: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error."}), 500


@app.route("/api/vision", methods=["POST"])
def vision_endpoint():
    try:
        image_bytes = None
        mime_type = "image/jpeg"
        destination = "Global / Any Destination"
        user_query = ""

        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"status": "error", "message": "No file selected."}), 400

            image_bytes = file.read()
            mime_type = file.mimetype or "image/jpeg"
            destination = request.form.get("destination", "Global / Any Destination")
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
            user_query = data.get("user_query", "")
        else:
            return jsonify({"status": "error", "message": "Invalid request format."}), 400

        image_svc = get_image_service()
        result = image_svc.analyze_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            destination=destination,
            user_query=user_query
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error handling /api/vision request: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to process image."}), 500


@app.route("/api/recommendations", methods=["POST"])
def get_recommendations_endpoint():
    try:
        data = request.get_json() or {}
        destination = data.get("destination", "Hyderabad")
        interests = data.get("interests", [])
        budget_level = data.get("budget_level", "Moderate")
        traveller_type = data.get("traveller_type", "Solo")
        lang_code = data.get("lang", Config.DEFAULT_LANGUAGE)

        rec_service = get_recommendation_service()
        results = rec_service.get_recommendations(
            destination=destination,
            interests=interests,
            budget_level=budget_level,
            traveller_type=traveller_type,
            lang_code=lang_code
        )

        return jsonify({"status": "success", "data": results}), 200

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to generate recommendations."}), 500


@app.route("/api/itinerary", methods=["POST"])
def generate_itinerary_endpoint():
    try:
        data = request.get_json() or {}
        destination = data.get("destination", "Hyderabad")
        num_days = int(data.get("num_days", 2))
        budget_level = data.get("budget_level", "Moderate")
        traveller_type = data.get("traveller_type", "Solo")
        interests = data.get("interests", ["History", "Food"])
        lang_code = data.get("lang", Config.DEFAULT_LANGUAGE)

        itinerary_svc = get_itinerary_service()
        result = itinerary_svc.generate_itinerary(
            destination=destination,
            num_days=num_days,
            budget_level=budget_level,
            traveller_type=traveller_type,
            interests=interests,
            lang_code=lang_code
        )

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to generate itinerary."}), 500


@app.route("/api/translate", methods=["POST"])
def translate_endpoint():
    try:
        data = request.get_json() or {}
        text = data.get("text", "").strip()
        target_lang = data.get("target_lang", Config.DEFAULT_LANGUAGE)
        destination = data.get("destination", "Global / Any Destination")

        if not text:
            return jsonify({"status": "error", "message": "Text parameter is required."}), 400

        trans_svc = get_translation_service()
        result = trans_svc.translate_phrase(
            text=text,
            target_lang=target_lang,
            destination=destination
        )

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        logger.error(f"Error translating phrase: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to translate phrase."}), 500


@app.route("/api/emergency/locations", methods=["GET"])
def emergency_locations_endpoint():
    try:
        em_svc = get_emergency_service()
        return jsonify({"status": "success", "data": em_svc.get_all_locations()}), 200
    except Exception as e:
        logger.error(f"Error fetching emergency locations: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to fetch locations."}), 500


@app.route("/api/emergency", methods=["GET", "POST"])
def emergency_endpoint():
    try:
        if request.method == "POST":
            data = request.get_json() or {}
        else:
            data = request.args

        country = data.get("country", "India")
        state = data.get("state", "Telangana (Hyderabad)")

        em_svc = get_emergency_service()
        result = em_svc.get_emergency_contacts(country=country, state=state)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        logger.error(f"Error fetching emergency contacts: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to fetch emergency contacts."}), 500


@app.route("/api/vision", methods=["POST"])
def vision_endpoint():
    try:
        image_bytes = None
        mime_type = "image/jpeg"
        target_lang = Config.DEFAULT_LANGUAGE
        destination = "Global / Any Destination"
        user_query = ""

        # Form Upload
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"status": "error", "message": "No file selected."}), 400

            image_bytes = file.read()
            mime_type = file.mimetype or "image/jpeg"
            target_lang = request.form.get("target_lang", Config.DEFAULT_LANGUAGE)
            destination = request.form.get("destination", "Global / Any Destination")
            user_query = request.form.get("user_query", "")

        # Base64 JSON Payload
        elif request.is_json:
            data = request.get_json() or {}
            b64_str = data.get("image_base64", "")
            if not b64_str:
                return jsonify({"status": "error", "message": "Missing image data."}), 400

            if "," in b64_str:
                b64_str = b64_str.split(",")[1]

            image_bytes = base64.b64decode(b64_str)
            mime_type = data.get("mime_type", "image/jpeg")
            target_lang = data.get("target_lang", Config.DEFAULT_LANGUAGE)
            destination = data.get("destination", "Global / Any Destination")
            user_query = data.get("user_query", "")

        else:
            return jsonify({"status": "error", "message": "Invalid request format."}), 400

        image_svc = get_image_service()
        result = image_svc.analyze_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            target_lang=target_lang,
            destination=destination,
            user_query=user_query
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error handling /api/vision request: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Failed to process image."}), 500


@app.errorhandler(404)
def handle_404(error):
    return jsonify({"status": "error", "message": "Resource not found."}), 404


@app.errorhandler(500)
def handle_500(error):
    return jsonify({"status": "error", "message": "Internal server error."}), 500


if __name__ == "__main__":
    logger.info(f"Launching TravelMate AI on port {Config.PORT}...")
    app.run(host="0.0.0.0", port=Config.PORT, debug=(Config.FLASK_ENV == "development"))