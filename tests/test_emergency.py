"""
TravelMate AI — Emergency Service Test Suite
Tests ground-truth emergency directory lookups and fallback handling.
"""

import pytest
from services.emergency_service import EmergencyService


@pytest.fixture
def em_service():
    """Provides instance of EmergencyService."""
    return EmergencyService()


def test_get_emergency_contacts_hyderabad(em_service):
    """Verifies correct ground-truth police and ambulance contacts for Hyderabad, India."""
    result = em_service.get_emergency_contacts(country="India", city="Hyderabad", lang_code="en")
    assert result["country"] == "India"
    assert result["city"] == "Hyderabad"
    contacts = result["contacts"]
    assert "police" in contacts
    assert "ambulance" in contacts
    assert contacts["police"] in ["100 / 112", "112"]


def test_get_emergency_contacts_fallback(em_service):
    """Verifies fallback contacts for unlisted city."""
    result = em_service.get_emergency_contacts(country="UnknownCountry", city="UnknownCity", lang_code="en")
    contacts = result["contacts"]
    assert contacts["police"] == "112"
    assert "tourist_helpline" in contacts