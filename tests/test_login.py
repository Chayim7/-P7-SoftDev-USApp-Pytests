"""
Tests for GitHub Issue #1: Invalid email login handling

These tests verify:
- Valid email login succeeds with HTTP 200 and shows welcome page
- Invalid email login returns HTTP 401 with error message (no crash)
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
def mock_clubs_data(monkeypatch):
    """Mock the get_clubs function to return a small fixture list."""
    def _mock_get_clubs():
        return [
            {"name": "Test Club", "email": "valid@test.com", "points": "10"},
        ]
    monkeypatch.setattr("server.get_clubs", _mock_get_clubs)


class TestLoginValidEmail:
    """Tests for valid email login."""

    def test_valid_email_returns_200(self, client, mock_clubs_data):
        """A valid email login should return HTTP 200 after redirect."""
        response = client.post(
            "/login",
            data={"email": "valid@test.com"},
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_valid_email_shows_welcome_content(self, client, mock_clubs_data):
        """A valid email login should display the welcome page with user email."""
        response = client.post(
            "/login",
            data={"email": "valid@test.com"},
            follow_redirects=True
        )
        assert b"Welcome" in response.data
        assert b"valid@test.com" in response.data

    def test_valid_email_shows_points(self, client, mock_clubs_data):
        """A valid email login should display the club's available points."""
        response = client.post(
            "/login",
            data={"email": "valid@test.com"},
            follow_redirects=True
        )
        assert b"Points available:" in response.data


class TestLoginInvalidEmail:
    """Tests for invalid email login - GitHub Issue #1."""

    def test_invalid_email_returns_401(self, client, mock_clubs_data):
        """An invalid email login should return HTTP 401 Unauthorized."""
        response = client.post(
            "/login",
            data={"email": "unknown@invalid.com"},
            follow_redirects=False
        )
        assert response.status_code == 401

    def test_invalid_email_does_not_crash(self, client, mock_clubs_data):
        """An invalid email login should NOT crash the application."""
        # This test passes if no exception is raised
        response = client.post(
            "/login",
            data={"email": "unknown@invalid.com"},
            follow_redirects=False
        )
        # Should get a response (not a 500 server error)
        assert response.status_code != 500

    def test_invalid_email_shows_error_message(self, client, mock_clubs_data):
        """An invalid email login should display a clear error message."""
        response = client.post(
            "/login",
            data={"email": "unknown@invalid.com"},
            follow_redirects=False
        )
        # Check that an error message is present in the response
        assert b"error" in response.data.lower() or b"invalid" in response.data.lower() or b"not found" in response.data.lower()

    def test_empty_email_returns_401(self, client, mock_clubs_data):
        """An empty email should return HTTP 401."""
        response = client.post(
            "/login",
            data={"email": ""},
            follow_redirects=False
        )
        assert response.status_code == 401
