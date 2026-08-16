"""
TravelMate AI — Recommendation Engine Test Suite
Tests interest scoring logic, budget filtering, and ranking algorithms.
"""

import pytest
from services.recommendation_service import RecommendationService


@pytest.fixture
def rec_service():
    """Provides instance of RecommendationService."""
    return RecommendationService()


def test_score_attraction_perfect_match(rec_service):
    """Verifies attraction scoring when interests, budget, and traveller type match."""
    attraction = {
        "interests": ["History", "Culture"],
        "budget_level": "Budget",
        "traveller_types": ["Solo"],
        "popularity_score": 0.9
    }
    preferences = {
        "interests": ["History", "Culture"],
        "budget_level": "Budget",
        "traveller_type": "Solo"
    }
    score = rec_service.score_attraction(attraction, preferences)
    # Weight breakdown: Interests (0.4) + Budget (0.3) + Traveller (0.2) + Popularity (0.09) = ~0.99
    assert score >= 0.9


def test_score_attraction_partial_match(rec_service):
    """Verifies lower score for partial matching attributes."""
    attraction = {
        "interests": ["Adventure"],
        "budget_level": "Premium",
        "traveller_types": ["Family"],
        "popularity_score": 0.8
    }
    preferences = {
        "interests": ["History"],
        "budget_level": "Budget",
        "traveller_type": "Solo"
    }
    score = rec_service.score_attraction(attraction, preferences)
    assert score < 0.5


def test_recommendation_filtering_hyderabad(rec_service):
    """Verifies top attractions filtered specifically for Hyderabad."""
    result = rec_service.get_recommendations(
        destination="Hyderabad",
        interests=["History"],
        budget_level="Budget",
        traveller_type="Solo",
        limit=3
    )
    assert result["destination"] == "Hyderabad"
    assert len(result["recommendations"]) <= 3
    assert any("Charminar" in r["name"] or "Golconda" in r["name"] for r in result["recommendations"])