"""
Tests for GitHub Issue #4: Cannot book spots in past competitions

Clubs must NOT be able to book spots in competitions whose date is in the past.

These tests verify:
- Booking a past competition is rejected with error message
- Booking a future competition is allowed
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
def mock_past_competition(monkeypatch):
    """Mock competitions data with a PAST competition."""
    def _mock_get_clubs():
        return [
            {"name": "Time Club", "email": "time@club.com", "points": "10"},
        ]

    def _mock_get_competitions():
        return [
            {
                "name": "Old Competition",
                "date": "2020-01-01 10:00:00",
                "spotsAvailable": "20",
            },
        ]

    monkeypatch.setattr("server.get_clubs", _mock_get_clubs)
    monkeypatch.setattr("server.get_competitions", _mock_get_competitions)


@pytest.fixture
def mock_future_competition(monkeypatch):
    """Mock competitions data with a FUTURE competition."""
    def _mock_get_clubs():
        return [
            {"name": "Future Club", "email": "future@club.com", "points": "10"},
        ]

    def _mock_get_competitions():
        return [
            {
                "name": "Future Competition",
                "date": "2030-01-01 10:00:00",
                "spotsAvailable": "20",
            },
        ]

    monkeypatch.setattr("server.get_clubs", _mock_get_clubs)
    monkeypatch.setattr("server.get_competitions", _mock_get_competitions)


class TestPastCompetitionBooking:
    """Tests for past competition booking prevention - Issue #4."""

    def test_past_competition_booking_rejected(self, client, mock_past_competition):
        """Booking a past competition should be rejected."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Time Club", "email": "time@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Old Competition", "spots": "3"},
            follow_redirects=True
        )

        # Should NOT show success message
        assert b"booking complete" not in response.data.lower()

    def test_past_competition_shows_error(self, client, mock_past_competition):
        """Booking a past competition should show an error message."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Time Club", "email": "time@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Old Competition", "spots": "3"},
            follow_redirects=True
        )

        # Should show error message about past competition
        data_lower = response.data.lower()
        assert (b"error" in data_lower or
                b"past" in data_lower or
                b"already" in data_lower or
                b"ended" in data_lower or
                b"over" in data_lower)

    def test_past_competition_no_point_change(self, client, mock_past_competition):
        """When booking past competition fails, club points should NOT change."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Time Club", "email": "time@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Old Competition", "spots": "3"},
            follow_redirects=True
        )

        # Points should still be 10 (unchanged)
        assert b"Points available: 10" in response.data

    def test_past_competition_no_spots_change(self, client, mock_past_competition):
        """When booking past competition fails, spotsAvailable should NOT change."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Time Club", "email": "time@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Old Competition", "spots": "3"},
            follow_redirects=True
        )

        # Spots should still be 20 (unchanged)
        assert b"20" in response.data


class TestFutureCompetitionBooking:
    """Tests for future competition booking - should be allowed."""

    def test_future_competition_booking_allowed(self, client, mock_future_competition):
        """Booking a future competition should succeed."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Future Club", "email": "future@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )

        # Should show success message
        assert b"booking complete" in response.data.lower()

    def test_future_competition_deducts_points(self, client, mock_future_competition):
        """Booking a future competition should deduct points."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Future Club", "email": "future@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )

        # Points should be 7 (10 - 3)
        assert b"Points available: 7" in response.data

    def test_future_competition_reduces_spots(self, client, mock_future_competition):
        """Booking a future competition should reduce spotsAvailable."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Future Club", "email": "future@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )

        # Spots should be 17 (20 - 3)
        assert b"17" in response.data
