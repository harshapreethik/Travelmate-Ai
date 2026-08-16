# TravelMate AI — AI Design & Safety Controls

## 1. Prompt Engineering Strategy

### System Instructions
Each AI service loads a distinct prompt template from `prompts/`. Prompts explicitly instruct the model on:
- Persona (expert, polite multilingual travel guide)
- Destination context locking
- Language output target
- Safety and hallucination boundaries

### Temperature Tuning
- **Chat & Itineraries (`temperature=0.7`):** Balanced creativity for natural conversation and narrative generation.
- **Vision & OCR (`temperature=0.4`):** Low variance for precise text extraction from images.

## 2. Safety & Guardrails

1. **Hallucination Suppression:**
   System prompts contain explicit rules forbidding the model from inventing ticket prices or emergency contact numbers. Critical facts are served directly from JSON files.

2. **Non-Tourism Refusal:**
   Queries regarding unsafe or non-travel topics are politely redirected to travel guidance.

3. **Ground-Truth Emergency Directives:**
   Emergency phone numbers bypass the generative layer entirely to guarantee safety.