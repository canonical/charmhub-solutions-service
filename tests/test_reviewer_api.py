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
def test_approve_name(mock_logic, client):
    mock_logic.return_value = {"name": "solution1", "status": "pending_metadata_submission"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/approve-name")
    assert response.status_code == 200
    assert response.get_json()["name"] == "solution1"
    assert response.get_json()["status"] == "pending_metadata_submission"
    mock_logic.assert_called_once_with("solution1")


@patch("app.reviewer.api.approve_solution_metadata")
def test_approve_metadata(mock_logic, client):
    mock_logic.return_value = {"name": "solution1", "status": "published"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/approve-metadata")

    assert response.status_code == 200
    assert response.get_json()["status"] == "published"
    mock_logic.assert_called_once_with("solution1")


@patch("app.reviewer.api.unpublish_solution")
def test_unpublish_solution(mock_logic, client):
    mock_logic.return_value = {"name": "solution1", "status": "unpublished"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/unpublish")

    assert response.status_code == 200
    assert response.get_json()["status"] == "unpublished"
    mock_logic.assert_called_once_with("solution1")


@patch("app.reviewer.api.republish_solution")
def test_republish_solution(mock_logic, client):
    mock_logic.return_value = {"name": "solution1", "status": "published"}
    with patch("app.public.auth.g") as mock_g:
        mock_g.user = {"teams": ["charmhub-solution-reviewers"]}
        response = client.get("/api/reviewer/solution1/republish")

    assert response.status_code == 200
    assert response.get_json()["status"] == "published"
    mock_logic.assert_called_once_with("solution1")
