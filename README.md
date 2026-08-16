# TravelMate AI — Multilingual Tourist Assistant 🧭✨

> **Cognizant Hackathon Project Submission**  
> *Empowering global travelers with instant, zero-hallucination recommendations, day-by-day itineraries, real-time phrase translation, multimodal vision OCR, and ground-truth emergency support.*

---

## 🌟 Key Features

1. **Multilingual AI Travel Guide (`/api/chat`):**
   - Context-aware conversation in 9 languages (English, Hindi, Telugu, Tamil, Kannada, Malayalam, Spanish, French, German).
   - Powered by the official `google-genai` SDK and `gemini-flash-latest`.

2. **Hybrid Recommendation Engine (`/api/recommendations`):**
   - **Deterministic Python Layer:** Scores attractions by interests, budget level, and traveler type from ground-truth local datasets (`data/attractions.json`).
   - **Generative AI Layer:** Enriches recommendations with localized cultural insights and insider tips without hallucinating pricing or locations.

3. **Custom Day-by-Day Itinerary Builder (`/api/itinerary`):**
   - Generates realistic, time-partitioned daily plans (Morning, Afternoon, Evening) adapted to trip duration, budget, and travel style.

4. **Multimodal Vision OCR & Menu Reader (`/api/vision`):**
   - Analyzes uploaded photos of street signs, historical plaques, and foreign menus.
   - Extracts text via OCR, translates into the user's preferred language, and provides dietary alerts (Vegetarian, Halal, Allergens).

5. **Real-time Phrase Translator & Etiquette Guide (`/api/translate`):**
   - Provides translated travel phrases accompanied by phonetic pronunciation guides and destination-specific cultural etiquette tips.

6. **Zero-Hallucination Emergency Directory (`/api/emergency`):**
   - Direct lookup for verified local police, ambulance, fire, and tourist helpline numbers, accompanied by Gemini safety advice.

---

## 🛠️ Tech Stack & Architecture

- **Backend Framework:** Python 3.11+, Flask 3.0+
- **AI SDK & Model:** Google GenAI SDK (`google-genai`), Gemini 2.5 Flash (`gemini-flash-latest`)
- **Frontend UI:** Responsive Bootstrap 5, Async JavaScript (`fetch`), Custom CSS
- **Testing Suite:** `pytest` (API routes, scoring algorithms, emergency lookups)
- **Ground-Truth Data:** Structured JSON schemas (`destinations.json`, `attractions.json`, `emergency_contacts.json`)