"""
Tests for GitHub Issue #6: Public Points Board

There must be a public page accessible WITHOUT login that displays
a list of all clubs and their current number of points.

These tests verify:
- /points route returns HTTP 200 without authentication
- Page displays all clubs with their names and points
- No login is required to access the page
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
def mock_clubs_for_board(monkeypatch):
    """Mock clubs data for points board tests."""
    def _mock_get_clubs():
        return [
            {"name": "Alpha", "email": "a@alpha.com", "points": "5"},
            {"name": "Beta", "email": "b@beta.com", "points": "12"},
        ]

    monkeypatch.setattr("server.get_clubs", _mock_get_clubs)


class TestPointsBoard:
    """Tests for the public points board - Issue #6."""

    def test_points_board_public_access(self, client, mock_clubs_for_board):
        """GET /points should return HTTP 200 without authentication."""
        response = client.get("/points")
        assert response.status_code == 200

    def test_points_board_shows_clubs_and_points(self, client, mock_clubs_for_board):
        """Points board should display all club names and their points."""
        response = client.get("/points")

        # Check that both club names are present
        assert b"Alpha" in response.data
        assert b"Beta" in response.data

        # Check that both point values are present
        assert b"5" in response.data
        assert b"12" in response.data

    def test_points_board_no_login_required(self, client, mock_clubs_for_board):
        """Accessing /points should NOT require session['club']."""
        # Ensure no session is set
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/points")

        # Should still return 200 OK without any login
        assert response.status_code == 200
        # Should not redirect to login page
        assert b"Please enter your secretary email" not in response.data

    def test_points_board_sorted_by_points_descending(self, client, mock_clubs_for_board):
        """Points board should list clubs in descending order of points (nice-to-have)."""
        response = client.get("/points")

        # Beta (12 points) should appear before Alpha (5 points)
        data = response.data.decode()
        beta_pos = data.find("Beta")
        alpha_pos = data.find("Alpha")

        # Beta should come before Alpha in the page
        assert beta_pos < alpha_pos, "Clubs should be sorted by points in descending order"
