"""
TravelMate AI — Emergency & Safety Service
Provides instant, zero-hallucination ground-truth emergency directory with in-memory caching.
"""

import json
import logging
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class EmergencyService:
    def __init__(self):
        self.emergency_file = Config.EMERGENCY_FILE
        # In-memory cache loaded once at startup
        self.data_cache = self._load_data()

    def _load_data(self) -> dict:
        """Loads and caches emergency directory from JSON."""
        try:
            path = Path(self.emergency_file)
            if not path.exists():
                logger.warning(f"Emergency file missing at {self.emergency_file}")
                return {}
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info("Emergency directory cached in-memory successfully.")
                return data
        except Exception as e:
            logger.error(f"Failed to load emergency contacts: {e}")
            return {}

    def get_all_locations(self) -> dict:
        """Returns list of countries and their available states/regions."""
        locations = {}
        for country, states in self.data_cache.items():
            locations[country] = list(states.keys())
        return locations

    def get_emergency_contacts(self, country: str = "India", state: str = "National") -> dict:
        """
        Fetches instant zero-latency ground-truth emergency contacts from cache.
        """
        country_data = self.data_cache.get(country, {})
        contacts = country_data.get(state)

        # Fallback to national numbers if state is not specified
        if not contacts and "National" in country_data:
            contacts = country_data["National"]

        # Universal fallback
        if not contacts:
            contacts = {
                "police": "112",
                "ambulance": "112 / 108",
                "fire": "112",
                "tourist_helpline": "112",
                "safety_note": "Universal international emergency number: Dial 112."
            }

        return {
            "country": country,
            "state": state,
            "contacts": contacts
        }

# Singleton accessor
_emergency_service = None

def get_emergency_service() -> EmergencyService:
    global _emergency_service
    if _emergency_service is None:
        _emergency_service = EmergencyService()
    return _emergency_service