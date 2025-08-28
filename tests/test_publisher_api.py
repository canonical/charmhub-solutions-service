import pytest
from unittest.mock import patch
from flask import Flask
from app.publisher.api import publisher_bp


@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    app = Flask(__name__)
    # secret key for testing
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.register_blueprint(publisher_bp, url_prefix="/api/publisher")
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.get_solutions_by_lp_teams")
def test_get_publisher_solutions(
    mock_get_solutions_by_lp_teams, mock_decode_jwt_token, client
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1", "team2"]
    }
    
    mock_get_solutions_by_lp_teams.return_value = [
        {"name": "solution1", "publisher": "team1"},
        {"name": "solution2", "publisher": "team2"},
    ]
    
    response = client.get("/api/publisher/solutions", headers={
        "Authorization": "Bearer fake token"
    })
        
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["name"] == "solution1"
    mock_get_solutions_by_lp_teams.assert_called_once_with(["team1", "team2"])


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.create_empty_solution")
@patch("app.publisher.api.get_solution_by_name")
def test_register_solution(
    mock_get_solution_by_name, mock_create_empty_solution, mock_decode_jwt_token, client
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1", "team2"]
    }
    
    mock_get_solution_by_name.return_value = None
    mock_create_empty_solution.return_value = {
        "name": "new-solution",
        "publisher": "team1",
        "description": "Test description"
    }
    
    response = client.post("/api/publisher/solutions", json={
        "name": "new-solution",
        "publisher": "team1", 
        "description": "Test description",
        "creator_email": "test@example.com",
        "mattermost_handle": "@testuser",
        "matrix_handle": "@testuser:matrix.org"
    }, headers={"Authorization": "Bearer fake token"})
        
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "new-solution"
    mock_create_empty_solution.assert_called_once_with(
        name="new-solution",
        publisher="team1",
        description="Test description",
        creator_email="test@example.com",
        mattermost_handle="@testuser",
        matrix_handle="@testuser:matrix.org"
    )


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.get_solution_by_name")
def test_register_solution_duplicate_name(mock_get_solution_by_name, mock_decode_jwt_token, client):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"]
    }
    
    mock_get_solution_by_name.return_value = {"name": "existing-solution"}
    
    response = client.post("/api/publisher/solutions", json={
        "name": "existing-solution",
        "publisher": "team1",
        "description": "Test description",
        "creator_email": "test@example.com"
    }, headers={"Authorization": "Bearer fake token"})
        
    assert response.status_code == 400
    data = response.get_json()
    assert "already exists" in data["error"]


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.update_solution_metadata")
@patch("app.publisher.api.get_solution_by_name_and_rev")
def test_update_solution_revision_1(mock_get_solution_by_name_and_rev, mock_update_solution_metadata, mock_decode_jwt_token, client):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"]
    }
    
    mock_get_solution_by_name_and_rev.return_value = {
        "name": "test-solution",
        "revision": 1,
        "publisher": {"username": "team1"}
    }
    mock_update_solution_metadata.return_value = {
        "name": "test-solution",
        "revision": 1,
        "status": "pending_metadata_review",
        "title": "Updated Title"
    }
    
    response = client.patch("/api/publisher/solutions/test-solution/1", json={
        "title": "Updated Title",
        "description": "Updated description"
    }, headers={"Authorization": "Bearer fake token"})
        
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "pending_metadata_review"
    mock_update_solution_metadata.assert_called_once_with(
        "test-solution", 1, {"title": "Updated Title", "description": "Updated description"}
    )


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.update_solution_metadata")
@patch("app.publisher.api.get_solution_by_name_and_rev")
def test_update_solution_revision_greater_than_1(mock_get_solution_by_name_and_rev, mock_update_solution_metadata, mock_decode_jwt_token, client):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"]
    }
    
    mock_get_solution_by_name_and_rev.return_value = {
        "name": "test-solution",
        "revision": 2,
        "publisher": {"username": "team1"}
    }
    mock_update_solution_metadata.return_value = {
        "name": "test-solution",
        "revision": 2,
        "status": "published",
        "title": "Updated Title"
    }
    
    response = client.patch("/api/publisher/solutions/test-solution/2", json={
        "title": "Updated Title"
    }, headers={"Authorization": "Bearer fake token"})
        
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "published"


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.create_empty_solution")
@patch("app.publisher.api.get_solution_by_name")
@patch("app.publisher.api.update_solution_metadata")
@patch("app.publisher.api.get_solution_by_name_and_rev")
@patch("app.reviewer.logic.approve_solution_name")
def test_complete_solution_creation_flow(
    mock_approve_name, 
    mock_get_solution_by_name_and_rev,
    mock_update_metadata,
    mock_get_solution_by_name, 
    mock_create_empty_solution,
    mock_decode_jwt_token,
    client
):
    """Test the complete solution creation workflow from registration to publication."""
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"]
    }
    
    # Step 1: register solution name (PENDING_NAME_REVIEW)
    mock_get_solution_by_name.return_value = None
    mock_create_empty_solution.return_value = {
        "name": "test-solution",
        "publisher": {"username": "team1"},
        "description": "Test description",
        "status": "pending_name_review",
        "revision": 1
    }
    
    response = client.post("/api/publisher/solutions", json={
        "name": "test-solution",
        "publisher": "team1",
        "description": "Test description",
        "creator_email": "test@example.com"
    }, headers={"Authorization": "Bearer fake token"})
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "test-solution"
    assert data["status"] == "pending_name_review"
    
    # Step 2: reviewer approves name (PENDING_NAME_REVIEW -> DRAFT)
    mock_approve_name.return_value = {
        "name": "test-solution",
        "status": "draft",
        "revision": 1
    }
    
    # Step 3: publisher submits metadata (DRAFT -> PENDING_METADATA_REVIEW)
    mock_get_solution_by_name_and_rev.return_value = {
        "name": "test-solution",
        "revision": 1,
        "publisher": {"username": "team1"}
    }
    mock_update_metadata.return_value = {
        "name": "test-solution",
        "revision": 1,
        "status": "pending_metadata_review",
        "title": "Test Solution Title",
        "summary": "Test summary"
    }
    
    response = client.patch("/api/publisher/solutions/test-solution/1", json={
        "title": "Test Solution Title",
        "summary": "Test summary"
    }, headers={"Authorization": "Bearer fake token"})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Test Solution Title"
    assert data["status"] == "pending_metadata_review"
    
    mock_create_empty_solution.assert_called_once_with(
        name="test-solution",
        publisher="team1",
        description="Test description",
        creator_email="test@example.com",
        mattermost_handle=None,
        matrix_handle=None
    )
