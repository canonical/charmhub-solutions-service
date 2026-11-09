import pytest
from unittest.mock import patch, Mock
from flask import Flask
from app.extensions import db
from app.public.api import public_bp
from app.public.logic import get_published_solution_by_hash
from app.models import (
    Creator,
    PlatformTypes,
    Publisher,
    Solution,
    SolutionStatus,
    Visibility,
)


@pytest.fixture
def app():
    """
    Create a Flask app for testing.
    """
    app = Flask(__name__)
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite://")
    db.init_app(app)
    app.register_blueprint(public_bp, url_prefix="/api")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


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


@patch("app.public.api.Solution")
def test_check_solution_name_exists(mock_solution, client):
    mock_solution.query.filter_by.return_value.first.return_value = {
        "name": "existing-solution"
    }
    response = client.get("/api/solutions/check-name/existing-solution")
    assert response.status_code == 200
    data = response.get_json()
    assert data["exists"] is True
    mock_solution.query.filter_by.assert_called_once_with(
        name="existing-solution"
    )


@patch("app.public.api.Solution")
def test_check_solution_name_does_not_exist(mock_solution, client):
    mock_solution.query.filter_by.return_value.first.return_value = None
    response = client.get("/api/solutions/check-name/new-solution")
    assert response.status_code == 200
    data = response.get_json()
    assert data["exists"] is False
    mock_solution.query.filter_by.assert_called_once_with(name="new-solution")


@patch("app.public.logic.serialize_public_solution")
@patch("app.public.logic.db.session")
def test_get_published_solution_by_hash_serves_draft(
    mock_session, mock_serialize_public_solution
):

    draft_solution = Mock(status=SolutionStatus.DRAFT)
    mock_session.query().filter().first.return_value = draft_solution
    mock_serialize_public_solution.return_value = {"status": "draft"}

    result = get_published_solution_by_hash("randomhash")

    assert result == {"status": "draft"}
    mock_serialize_public_solution.assert_called_once_with(draft_solution)


@pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.PRIVATE])
def test_published_preview_respects_discovery_visibility(client, visibility):
    solution = Solution(
        name="data-mesh",
        hash="previewhash",
        revision=1,
        title="Data Mesh",
        status=SolutionStatus.PUBLISHED,
        visibility=visibility,
        platform=PlatformTypes.KUBERNETES,
        publisher=Publisher(
            publisher_id="team", username="team", display_name="Team"
        ),
        creator=Creator(email="creator@example.com"),
    )
    db.session.add(solution)
    db.session.commit()

    preview = client.get("/api/solutions/preview/previewhash")
    assert preview.status_code == 200
    assert preview.get_json()["name"] == "data-mesh"
    assert "creator" not in preview.get_json()
    assert "approved_by" not in preview.get_json()

    listed = client.get("/api/solutions")
    search = client.get("/api/solutions/search?q=Data")
    by_name = client.get("/api/solutions/data-mesh")
    assert listed.status_code == 200
    assert search.status_code == 200
    if visibility == Visibility.PUBLIC:
        assert [item["name"] for item in listed.get_json()] == ["data-mesh"]
        assert [item["name"] for item in search.get_json()] == ["data-mesh"]
        assert by_name.status_code == 200
    else:
        assert listed.get_json() == []
        assert search.get_json() == []
        assert by_name.status_code == 404
