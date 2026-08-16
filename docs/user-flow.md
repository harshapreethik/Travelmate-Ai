# TravelMate AI — User Flow & UX Journey

This document details the end-to-end user navigation flow, tab-by-tab operational logic, and real-world user scenarios for TravelMate AI.

---

## 1. System Navigation Architecture

```text
                        [ Launch Application ]
                                  │
                       (Dashboard: index.html)
                                  │
       ┌──────────────┬───────────┼───────────┬──────────────┬──────────────┐
       ▼              ▼           ▼           ▼              ▼              ▼
[ Tab 1: Chat ] [ Tab 2: Recs ] [ Tab 3: Itin ] [ Tab 4: Vision ] [ Tab 5: Trans ] [ Tab 6: Emerg ]
       │              │           │           │              │              │
 Ask Question   Set Preferences  Input Days  Upload Photo   Enter Phrase   Select City
       │              │           │           │              │              │
  Gemini Reply   Scored List +   Day-by-Day  OCR + Trans +   Phonetics +   Verified Numbers
                 AI Insights       Plan      Dietary Tips   Etiquette Tip   + Safety Note



2. Tab-by-Tab User Flow
Tab 1: Multilingual AI Chat Guide (/api/chat)
1.User enters destination context (e.g., Hyderabad).

2.User selects global output language (e.g., Telugu, Hindi, English).

3.User types a general travel query.

4.Gemini returns localized, context-aware advice directly inside the chat window.

Tab 2: Hybrid Recommendation Engine (/api/recommendations)
1.User inputs destination, traveler style (Solo, Family, Couple), and budget (Budget, Moderate, Premium).

2.User selects preferred interest checkboxes (History, Food, Nature, Shopping).

3.System runs deterministic Python scoring against data/attractions.json.

4.Dashboard displays top-ranked cards with calculated match percentages alongside a Gemini AI cultural summary.

Tab 3: Day-by-Day Itinerary Builder (/api/itinerary)
1.User inputs target city and trip duration (1–14 days).

2.User sets budget level and traveler type.

3.System triggers Gemini to construct a structured schedule partitioned into Morning, Afternoon, and Evening slots.

Tab 4: Multimodal Vision OCR & Menu Reader (/api/vision)
1.User uploads/drags a photo of a restaurant menu, signboard, or plaque.

2.User optionally adds a specific question ("Are there vegetarian options?").

3.Gemini Vision extracts text via OCR, translates it into the user's selected language, and highlights dietary warnings or direction tips.

Tab 5: Real-time Travel Phrase Translator (/api/translate)
1.User enters a phrase (e.g., "How much does this cost?").

2.System translates the phrase into the selected language, provides an English-script phonetic guide, and adds a local cultural etiquette note.

Tab 6: Zero-Hallucination Emergency Support (/api/emergency)
1.User selects Country and City.

2.System bypasses generative generation to fetch verified local police, ambulance, fire, and tourist helpline numbers directly from ground-truth JSON files.

3.System appends Gemini safety advice for urgent situations.            



3. Real-World User Scenarios
Scenario A: Solo Backpacker Reading a Foreign Menu
Goal: Decode a local street food menu and avoid food allergens.

Journey: Navigates to Tab 4 (Vision) -> Uploads photo of menu -> Receives instant translation, item descriptions, and dietary alerts.

Scenario B: Family Planning a Weekend Getaway
Goal: Create a 2-day family-friendly itinerary for Hyderabad.

Journey: Navigates to Tab 3 (Itinerary) -> Inputs 2 Days, Moderate Budget, Family -> Gets a complete morning-to-night schedule.

Scenario C: Tourist Needing Urgent Medical Help
Goal: Access local ambulance and police numbers without searching unreliable blogs.

Journey: Navigates to Tab 6 (Emergency) -> Selects India / Hyderabad -> Instantly sees verified contacts (Police: 112, Ambulance: 108).