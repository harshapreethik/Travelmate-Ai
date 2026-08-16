# TravelMate AI — System Architecture & Technical Flow

## 1. Overview
TravelMate AI combines deterministic rule-based algorithms with generative AI (`gemini-flash-latest`). This hybrid approach prevents AI hallucination on critical travel facts (ticket prices, opening hours, emergency numbers) while leveraging Large Language Models for multilingual reasoning, menu OCR, and narrative generation.

## 2. Component Design

### A. Ground-Truth Data Layer (`data/`)
Static JSON datasets store validated destination details, attraction prices, categories, coordinates, and emergency phone numbers.

### B. Hybrid Recommendation Service (`services/recommendation_service.py`)
1. **Filtering:** Filters attractions matching the selected target city.
2. **Scoring Formula:**
   Score = (0.4 * InterestMatch) + (0.3 * BudgetMatch) + (0.2 * TravelerTypeMatch) + (0.1 * PopularityScore)
3. **Generative Enrichment:** Top ranked results are passed to Gemini to generate localized context and travel tips in the user's language.

### C. Multimodal Vision Pipeline (`services/image_service.py`)
Uploads are converted into `google.genai.types.Part.from_bytes()` payloads and passed directly to `gemini-flash-latest` with low temperature settings (`0.4`) for precise OCR and menu translation.