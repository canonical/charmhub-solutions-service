import pytest
from unittest.mock import patch
from flask import Flask
from app.reviewer.api import reviewer_bp


@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(reviewer_bp, url_prefix="/api/reviewer")
    app.app_context().push()
    return app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


@patch("app.reviewer.api.approve_solution_name")
def test_approve_name(mock_approve_solution_name, client):
    mock_approve_solution_name.return_value = {"name": "solution1"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/approve-name")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "solution1"
    mock_approve_solution_name.assert_called_once_with("solution1")


@patch("app.reviewer.api.approve_solution_metadata")
def test_approve_metadata(mock_approve_solution_metadata, client):
    mock_approve_solution_metadata.return_value = {"name": "solution1"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/approve-metadata")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "solution1"
    mock_approve_solution_metadata.assert_called_once_with("solution1")


@patch("app.reviewer.api.unpublish_solution")
def test_unpublish_solution(mock_unpublish_solution, client):
    mock_unpublish_solution.return_value = {"name": "solution1"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/unpublish")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "solution1"
    mock_unpublish_solution.assert_called_once_with("solution1")
