import os
from pathlib import Path
from dotenv import load_dotenv

# Absolute path to .env file in project root
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables into process
load_dotenv(dotenv_path=ENV_PATH, override=True)

class Config:
    # Flask Core Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "travelmate_dev_secret_key_2026")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("PORT", 5000))
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-flash-latest"  # Stable alias for active Flash model
    
    # Supported Multilingual Options
    DEFAULT_LANGUAGE = "en"
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "te": "Telugu (తెలుగు)",
        "ta": "Tamil (தமிழ்)",
        "kn": "Kannada (కన్నడ)",
        "ml": "Malayalam (മലയാളം)",
        "es": "Spanish (Español)",
        "fr": "French (Français)",
        "de": "German (Deutsch)"
    }
    
    # Dataset Configuration Paths
    DATA_DIR = BASE_DIR / "data"
    DESTINATIONS_FILE = DATA_DIR / "destinations.json"
    ATTRACTIONS_FILE = DATA_DIR / "attractions.json"
    EMERGENCY_FILE = DATA_DIR / "emergency_contacts.json"

    @classmethod
    def validate_config(cls):
        """Verifies environment readiness."""
        key = cls.GEMINI_API_KEY
        if not key or not isinstance(key, str) or len(key.strip()) < 10:
            print("⚠️ WARNING: GEMINI_API_KEY is missing or invalid in .env!")
            return False
            
        print("==================================================")
        print(f"✅ Configuration loaded successfully.")
        print(f"🤖 Selected Gemini Model: {cls.GEMINI_MODEL}")
        print(f"🔑 API Key Status: Present (Length: {len(key)})")
        print("==================================================")
        return True

if __name__ == "__main__":
    Config.validate_config()