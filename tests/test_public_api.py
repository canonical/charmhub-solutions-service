import pytest
from unittest.mock import patch
from flask import Flask
from app.public.api import public_bp


@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    app = Flask(__name__)
    app.register_blueprint(public_bp, url_prefix="/api")
    app.app_context().push()
    return app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


@patch("app.public.api.get_all_published_solutions")
def test_list_all_published_solutions(
    mock_get_all_published_solutions, client
):
    mock_get_all_published_solutions.return_value = [
        {"name": "solution1"},
        {"name": "solution2"},
    ]
    response = client.get("/api/solutions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["name"] == "solution1"
    assert data[1]["name"] == "solution2"
    mock_get_all_published_solutions.assert_called_once()


@patch("app.public.api.get_published_solution_by_name")
def test_get_solution_by_name(mock_get_published_solution_by_name, client):
    mock_get_published_solution_by_name.return_value = {"name": "solution1"}
    response = client.get("/api/solutions/solution1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "solution1"
    mock_get_published_solution_by_name.assert_called_once_with("solution1")


@patch("app.public.api.get_published_solution_by_name")
def test_get_solution_not_found(mock_get_published_solution_by_name, client):
    mock_get_published_solution_by_name.return_value = None
    response = client.get("/api/solutions/non-existent-solution")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Solution not found"
    mock_get_published_solution_by_name.assert_called_once_with(
        "non-existent-solution"
    )


@patch("app.public.api.search_published_solutions")
def test_search_solutions(mock_search_published_solutions, client):
    mock_search_published_solutions.return_value = [{"name": "solution1"}]
    response = client.get("/api/solutions/search?q=test")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "solution1"
    mock_search_published_solutions.assert_called_once_with("test")


@patch("app.public.api.search_published_solutions")
def test_search_solutions_no_query(mock_search_published_solutions, client):
    mock_search_published_solutions.return_value = []
    response = client.get("/api/solutions/search")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0
    mock_search_published_solutions.assert_called_once_with("")


@patch("app.public.api.search_published_solutions")
def test_search_solutions_no_results(mock_search_published_solutions, client):
    mock_search_published_solutions.return_value = []
    response = client.get("/api/solutions/search?q=non_existent_query")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0
    mock_search_published_solutions.assert_called_once_with(
        "non_existent_query"
    )
