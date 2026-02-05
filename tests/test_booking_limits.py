"""
Tests for GitHub Issue #3: Maximum 12 spots per competition limit

A single club may NOT book more than 12 spots per competition.

These tests verify:
- Booking exactly 12 spots succeeds (boundary case)
- Booking 13 spots is rejected with error message
"""

import pytest
from server import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_limit_data(monkeypatch):
    """
    Mock clubs and competitions data for booking limit tests.
    Club has plenty of points (50) and competition has plenty of spots (30).
    Uses a FUTURE date to avoid past-competition issues.
    """
    def _mock_get_clubs():
        return [
            {"name": "Rich Club", "email": "rich@club.com", "points": "50"},
        ]

    def _mock_get_competitions():
        return [
            {
                "name": "Big Competition",
                "date": "2030-01-01 10:00:00",
                "spotsAvailable": "30",
            },
        ]

    monkeypatch.setattr("server.get_clubs", _mock_get_clubs)
    monkeypatch.setattr("server.get_competitions", _mock_get_competitions)


class TestBookingLimit12Spots:
    """Tests for the 12 spots per competition limit - Issue #3."""

    def test_booking_12_spots_succeeds(self, client, mock_limit_data):
        """Booking exactly 12 spots should succeed (boundary case)."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Rich Club", "email": "rich@club.com", "points": "50"}

        response = client.post(
            "/book",
            data={"competition": "Big Competition", "spots": "12"},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b"booking complete" in response.data.lower()

    def test_booking_12_spots_deducts_points(self, client, mock_limit_data):
        """Booking 12 spots should deduct 12 points."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Rich Club", "email": "rich@club.com", "points": "50"}

        response = client.post(
            "/book",
            data={"competition": "Big Competition", "spots": "12"},
            follow_redirects=True
        )

        # Points should be 38 (50 - 12)
        assert b"Points available: 38" in response.data

    def test_booking_13_spots_rejected(self, client, mock_limit_data):
        """Booking 13 spots should be rejected (exceeds limit)."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Rich Club", "email": "rich@club.com", "points": "50"}

        response = client.post(
            "/book",
            data={"competition": "Big Competition", "spots": "13"},
            follow_redirects=True
        )

        # Should NOT show success message
        assert b"booking complete" not in response.data.lower()

    def test_booking_13_spots_shows_error(self, client, mock_limit_data):
        """Booking 13 spots should show an error message about the limit."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Rich Club", "email": "rich@club.com", "points": "50"}

        response = client.post(
            "/book",
            data={"competition": "Big Competition", "spots": "13"},
            follow_redirects=True
        )

        # Should show error message about limit
        data_lower = response.data.lower()
        assert (b"error" in data_lower or
                b"12" in data_lower or
                b"limit" in data_lower or
                b"maximum" in data_lower)

    def test_booking_13_spots_no_point_change(self, client, mock_limit_data):
        """When booking 13 spots fails, club points should NOT change."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Rich Club", "email": "rich@club.com", "points": "50"}

        response = client.post(
            "/book",
            data={"competition": "Big Competition", "spots": "13"},
            follow_redirects=True
        )

        # Points should still be 50 (unchanged)
        assert b"Points available: 50" in response.data

    def test_booking_13_spots_no_spots_change(self, client, mock_limit_data):
        """When booking 13 spots fails, competition spotsAvailable should NOT change."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Rich Club", "email": "rich@club.com", "points": "50"}

        response = client.post(
            "/book",
            data={"competition": "Big Competition", "spots": "13"},
            follow_redirects=True
        )

        # Spots should still be 30 (unchanged)
        assert b"30" in response.data
