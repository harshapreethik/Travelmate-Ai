# TravelMate AI — API Reference Manual

This document outlines all REST API endpoints provided by the Flask backend server.

---

## 1. System Health Check
* **Route:** `GET /api/health`
* **Purpose:** Verifies that the Flask server and Gemini API configuration are online.
* **Output:** Status report containing application name, version, and active Gemini model.

---

## 2. Multilingual Chat Assistant
* **Route:** `POST /api/chat`
* **Purpose:** Generates conversational responses to tourist questions in 9 supported languages.
* **Input Parameters:**
  - `message` (string): User's travel question.
  - `lang` (string): Target language code (e.g., "en", "hi", "te").
  - `destination` (string): Active city context (default: "Hyderabad").

---

## 3. Hybrid Recommendation Engine
* **Route:** `POST /api/recommendations`
* **Purpose:** Filters and ranks local attractions using Python scoring, enriched by Gemini travel insights.
* **Input Parameters:**
  - `destination` (string): Target city.
  - `interests` (list): Selected interests (e.g., ["History", "Food"]).
  - `budget_level` (string): "Budget", "Moderate", or "Premium".
  - `traveller_type` (string): "Solo", "Couple", "Family", or "Friends".
  - `lang` (string): Output language.

---

## 4. Day-by-Day Itinerary Planner
* **Route:** `POST /api/itinerary`
* **Purpose:** Builds custom multi-day travel schedules partitioned into Morning, Afternoon, and Evening activities.
* **Input Parameters:**
  - `destination` (string): Target city.
  - `num_days` (integer): Trip duration in days (1–14).
  - `budget_level` (string): Budget preference.
  - `traveller_type` (string): Traveler style.
  - `lang` (string): Output language.

---

## 5. Multimodal Vision & Menu Reader
* **Route:** `POST /api/vision`
* **Purpose:** Performs OCR and translation on uploaded images (menus, signboards, plaques) using Gemini Vision.
* **Input Parameters:**
  - `file` (multipart file upload): Image binary (JPEG/PNG).
  - `target_lang` (string): Language for translated output.
  - `destination` (string): City context.
  - `user_query` (string, optional): Specific question about the image.

---

## 6. Verified Emergency Directory
* **Route:** `GET /api/emergency`
* **Purpose:** Serves zero-hallucination local emergency numbers (police, ambulance, tourist hotline) from ground-truth JSON files.
* **Query Parameters:**
  - `country` (string): e.g., "India"
  - `city` (string): e.g., "Hyderabad"
  - `lang` (string): Language for safety advice.