import pytest
from unittest.mock import patch
from flask import Flask
from app.dashboard.routes import dashboard_bp


@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.app_context().push()
    return app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


@patch("app.dashboard.routes.approve_solution_name")
def test_approve_name(mock_logic, client):
    mock_logic.return_value = {"name": "solution1", "status": "draft"}
    with client.session_transaction() as session:
        session['openid'] = {'identity_url': 'test_user', 'email': 'test@example.com'}
    response = client.get("/solution1/approve-name")
    assert response.status_code == 200
    assert response.get_json()["name"] == "solution1"
    assert response.get_json()["status"] == "draft"
    mock_logic.assert_called_once_with("solution1")


@patch("app.dashboard.routes.approve_solution_metadata")
def test_approve_metadata(mock_logic, client):
    mock_logic.return_value = {"name": "solution1", "status": "published"}
    with client.session_transaction() as session:
        session['openid'] = {'identity_url': 'test_user', 'email': 'test@example.com'}
    response = client.get("/solution1/approve-metadata")

    assert response.status_code == 200
    assert response.get_json()["status"] == "published"
    mock_logic.assert_called_once_with("solution1")



