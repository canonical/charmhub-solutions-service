import pytest
from unittest.mock import patch, Mock
from flask import Flask
from app.publisher.api import publisher_bp
from app.exceptions import ValidationError


@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    app = Flask(__name__)
    # secret key for testing
    app.config["SECRET_KEY"] = "test-secret-key"
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
@patch("app.publisher.api.publisher_logic.get_solutions_by_lp_teams")
def test_get_publisher_solutions(
    mock_get_solutions_by_lp_teams, mock_decode_jwt_token, client
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1", "team2"],
    }

    mock_get_solutions_by_lp_teams.return_value = [
        {"name": "solution1", "publisher": "team1"},
        {"name": "solution2", "publisher": "team2"},
    ]

    response = client.get(
        "/api/publisher/solutions",
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["name"] == "solution1"
    mock_get_solutions_by_lp_teams.assert_called_once_with(["team1", "team2"])


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.publisher_logic.find_or_create_creator")
@patch("app.publisher.api.publisher_logic.register_solution_package")
def test_register_solution(
    mock_register_solution_package, mock_find_or_create_creator, mock_decode_jwt_token, client
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1", "team2"],
    }

    mock_creator = Mock(id=1)
    mock_find_or_create_creator.return_value = mock_creator

    mock_register_solution_package.return_value = {
        "name": "new-solution",
        "publisher": "team1",
        "summary": "Test summary",
    }

    response = client.post(
        "/api/publisher/solutions",
        json={
            "name": "new-solution",
            "publisher": "team1",
            "summary": "Test summary",
            "creator_email": "test@example.com",
            "mattermost_handle": "@testuser",
            "matrix_handle": "@testuser:matrix.org",
        },
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "new-solution"
    mock_find_or_create_creator.assert_called_once_with(
        "test@example.com",
        "@testuser",
        "@testuser:matrix.org",
    )
    mock_register_solution_package.assert_called_once_with(
        teams=["team1", "team2"],
        name="new-solution",
        publisher="team1",
        summary="Test summary",
        creator=mock_creator,
        title=None,
        platform="kubernetes",
    )


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.publisher_logic.find_or_create_creator")
@patch("app.publisher.api.publisher_logic.register_solution_package")
def test_register_solution_duplicate_name(
    mock_register_solution_package, mock_find_or_create_creator, mock_decode_jwt_token, client
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"],
    }

    mock_creator = Mock(id=1)
    mock_find_or_create_creator.return_value = mock_creator

    mock_register_solution_package.side_effect = ValidationError(
        [
            {
                "code": "already-registered",
                "message": "A solution with this name already exists",
            }
        ]
    )

    response = client.post(
        "/api/publisher/solutions",
        json={
            "name": "existing-solution",
            "publisher": "team1",
            "summary": "Test summary",
            "creator_email": "test@example.com",
        },
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error-list" in data
    assert data["error-list"][0]["code"] == "already-registered"


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.publisher_logic.update_solution_metadata")
@patch("app.publisher.api.publisher_logic.get_solution_by_name_and_rev")
def test_update_solution_revision_1(
    mock_get_solution_by_name_and_rev,
    mock_update_solution_metadata,
    mock_decode_jwt_token,
    client,
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"],
    }

    mock_get_solution_by_name_and_rev.return_value = {
        "name": "test-solution",
        "revision": 1,
        "publisher": {"username": "team1"},
    }
    mock_update_solution_metadata.return_value = {
        "name": "test-solution",
        "revision": 1,
        "status": "pending_metadata_review",
        "title": "Updated Title",
    }

    response = client.patch(
        "/api/publisher/solutions/test-solution/1",
        json={"title": "Updated Title", "description": "Updated description"},
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "pending_metadata_review"
    mock_update_solution_metadata.assert_called_once_with(
        "test-solution",
        1,
        {"title": "Updated Title", "description": "Updated description"},
    )


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.publisher_logic.update_solution_metadata")
@patch("app.publisher.api.publisher_logic.get_solution_by_name_and_rev")
def test_update_solution_revision_greater_than_1(
    mock_get_solution_by_name_and_rev,
    mock_update_solution_metadata,
    mock_decode_jwt_token,
    client,
):
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"],
    }

    mock_get_solution_by_name_and_rev.return_value = {
        "name": "test-solution",
        "revision": 2,
        "publisher": {"username": "team1"},
    }
    mock_update_solution_metadata.return_value = {
        "name": "test-solution",
        "revision": 2,
        "status": "published",
        "title": "Updated Title",
    }

    response = client.patch(
        "/api/publisher/solutions/test-solution/2",
        json={"title": "Updated Title"},
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "published"


@patch("app.public.auth.decode_jwt_token")
@patch("app.publisher.api.publisher_logic.find_or_create_creator")
@patch("app.publisher.api.publisher_logic.register_solution_package")
@patch("app.publisher.api.publisher_logic.update_solution_metadata")
@patch("app.publisher.api.publisher_logic.get_solution_by_name_and_rev")
@patch("app.reviewer.logic.approve_solution_name")
def test_complete_solution_creation_flow(
    mock_approve_name,
    mock_get_solution_by_name_and_rev,
    mock_update_metadata,
    mock_register_solution_package,
    mock_find_or_create_creator,
    mock_decode_jwt_token,
    client,
):
    """Test the complete solution creation workflow from registration to publication."""
    mock_decode_jwt_token.return_value = {
        "sub": "testuser",
        "teams": ["team1"],
    }

    mock_creator = Mock(id=1)
    mock_find_or_create_creator.return_value = mock_creator

    # Step 1: register solution name (PENDING_NAME_REVIEW)
    mock_register_solution_package.return_value = {
        "name": "test-solution",
        "publisher": {"username": "team1"},
        "summary": "Test summary",
        "status": "pending_name_review",
        "revision": 1,
    }

    response = client.post(
        "/api/publisher/solutions",
        json={
            "name": "test-solution",
            "publisher": "team1",
            "summary": "Test summary",
            "creator_email": "test@example.com",
        },
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "test-solution"
    assert data["status"] == "pending_name_review"

    # Step 2: reviewer approves name (PENDING_NAME_REVIEW -> DRAFT)
    mock_approve_name.return_value = {
        "name": "test-solution",
        "status": "draft",
        "revision": 1,
    }

    # Step 3: publisher submits metadata (DRAFT -> PENDING_METADATA_REVIEW)
    mock_get_solution_by_name_and_rev.return_value = {
        "name": "test-solution",
        "revision": 1,
        "publisher": {"username": "team1"},
    }
    mock_update_metadata.return_value = {
        "name": "test-solution",
        "revision": 1,
        "status": "pending_metadata_review",
        "title": "Test Solution Title",
        "summary": "Test summary",
    }

    response = client.patch(
        "/api/publisher/solutions/test-solution/1",
        json={"title": "Test Solution Title", "summary": "Test summary"},
        headers={"Authorization": "Bearer fake token"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Test Solution Title"
    assert data["status"] == "pending_metadata_review"

    mock_find_or_create_creator.assert_called_once_with(
        "test@example.com",
        None,
        None,
    )
    mock_register_solution_package.assert_called_once_with(
        teams=["team1"],
        name="test-solution",
        publisher="team1",
        summary="Test summary",
        creator=mock_creator,
        title=None,
        platform="kubernetes",
    )
