import os
from dotenv import load_dotenv
from google import genai

# Load the API key from your .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: Could not find GEMINI_API_KEY in .env file")
else:
    client = genai.Client(api_key=api_key)
    print("--- AVAILABLE MODELS FOR YOUR ACCOUNT ---")
    try:
        for model in client.models.list():
            # Only print models that support text generation
            if "generateContent" in getattr(model, "supported_actions", []):
                print(model.name)
            elif not hasattr(model, "supported_actions"): # Fallback if SDK varies
                print(model.name)
    except Exception as e:
        print(f"Failed to list models: {e}")