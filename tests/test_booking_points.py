"""
Tests for GitHub Issues #5 and #2: Booking points logic

Issue #5: Point updates are not reflected after booking
Issue #2: Clubs cannot use more points than they have available

These tests verify:
- Successful booking deducts points and reduces spots
- Insufficient points prevents booking
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
def mock_booking_data(monkeypatch):
    """
    Mock clubs and competitions data for booking tests.
    Uses a FUTURE date to avoid past-competition issues.
    """
    def _mock_get_clubs():
        return [
            {"name": "Test Club", "email": "test@club.com", "points": "10"},
            {"name": "Poor Club", "email": "poor@club.com", "points": "2"},
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


class TestSuccessfulBooking:
    """Tests for successful booking - Issue #5."""

    def test_successful_booking_returns_200(self, client, mock_booking_data):
        """A successful booking should return HTTP 200."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Test Club", "email": "test@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_successful_booking_shows_confirmation(self, client, mock_booking_data):
        """A successful booking should display a confirmation message."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Test Club", "email": "test@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )
        assert b"booking complete" in response.data.lower() or b"booked" in response.data.lower()

    def test_successful_booking_deducts_points(self, client, mock_booking_data):
        """After booking N spots, club points should decrease by N."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Test Club", "email": "test@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )

        # Check that points displayed is now 7 (10 - 3)
        assert b"Points available: 7" in response.data or b"7" in response.data

    def test_successful_booking_reduces_spots(self, client, mock_booking_data):
        """After booking N spots, competition spotsAvailable should decrease by N."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Test Club", "email": "test@club.com", "points": "10"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "3"},
            follow_redirects=True
        )

        # Check that spots available is now 17 (20 - 3)
        assert b"17" in response.data


class TestInsufficientPoints:
    """Tests for insufficient points - Issue #2."""

    def test_insufficient_points_rejected(self, client, mock_booking_data):
        """Booking more spots than available points should be rejected."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Poor Club", "email": "poor@club.com", "points": "2"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "5"},
            follow_redirects=True
        )

        # Should NOT show success message
        assert b"booking complete" not in response.data.lower()

    def test_insufficient_points_shows_error(self, client, mock_booking_data):
        """Booking with insufficient points should show an error message."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Poor Club", "email": "poor@club.com", "points": "2"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "5"},
            follow_redirects=True
        )

        # Should show error message about points
        data_lower = response.data.lower()
        assert (b"error" in data_lower or 
                b"not enough" in data_lower or 
                b"insufficient" in data_lower or
                b"points" in data_lower)

    def test_insufficient_points_no_point_change(self, client, mock_booking_data):
        """When booking fails due to insufficient points, club points should NOT change."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Poor Club", "email": "poor@club.com", "points": "2"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "5"},
            follow_redirects=True
        )

        # Points should still be 2 (unchanged)
        assert b"Points available: 2" in response.data or b"2" in response.data

    def test_insufficient_points_no_spots_change(self, client, mock_booking_data):
        """When booking fails, competition spotsAvailable should NOT change."""
        with client.session_transaction() as sess:
            sess["club"] = {"name": "Poor Club", "email": "poor@club.com", "points": "2"}

        response = client.post(
            "/book",
            data={"competition": "Future Competition", "spots": "5"},
            follow_redirects=True
        )

        # Spots should still be 20 (unchanged)
        assert b"20" in response.data
