import pytest
from flask import Flask

from app.dashboard.routes import dashboard_bp
from app.extensions import db
from app.models import (
    Creator,
    PlatformTypes,
    Publisher,
    Solution,
    SolutionStatus,
    Visibility,
)
from app.public.api import public_bp
from app.public.logic import get_published_solution_by_name
from app.publisher.api import publisher_bp


@pytest.fixture
def app():
    app = Flask(__name__, template_folder="../app/templates")
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI="sqlite://",
    )
    db.init_app(app)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(public_bp, url_prefix="/api")
    app.register_blueprint(publisher_bp, url_prefix="/api/publisher")

    with app.app_context():
        db.create_all()
        publisher = Publisher(
            publisher_id="team", username="team", display_name="Team"
        )
        creator = Creator(email="creator@example.com")
        revisions = [
            (1, "Old revision", SolutionStatus.UNPUBLISHED),
            (2, "Live revision", SolutionStatus.PUBLISHED),
            (3, "Draft revision", SolutionStatus.DRAFT),
        ]
        for revision, title, status in revisions:
            db.session.add(Solution(
                name="solution",
                hash=f"hash{revision}",
                revision=revision,
                title=title,
                status=status,
                visibility=Visibility.PUBLIC,
                platform=PlatformTypes.KUBERNETES,
                publisher=publisher,
                creator=creator,
            ))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session["openid"] = {
            "identity_url": "reviewer",
            "email": "reviewer@example.com",
        }
    return client


@pytest.fixture
def unpublish_form(client):
    client.get("/solution/unpublish")
    with client.session_transaction() as session:
        token = session["solution_action_csrf_token"]
    solution = Solution.query.filter_by(revision=2).one()
    return {"csrf_token": token, "solution_id": solution.id}


def test_unpublish_retains_solution_in_archive(client, unpublish_form):
    response = client.post("/solution/unpublish", data=unpublish_form)

    assert response.status_code == 302
    assert response.location == "/"
    solution = Solution.query.filter_by(revision=2).one()
    assert solution.status == SolutionStatus.UNPUBLISHED
    assert solution.visibility == Visibility.PRIVATE
    assert Solution.query.count() == 3
    assert Solution.query.filter_by(revision=3).one().status == SolutionStatus.DRAFT
    assert get_published_solution_by_name("solution") is None
    assert b"Live revision" in client.get("/archived").data


@pytest.mark.parametrize("path", ["/", "/archived", "/solution/unpublish"])
def test_dashboard_pages_require_login(app, path):
    response = app.test_client().get(path)

    assert response.status_code == 302
    assert response.location.startswith("/login?next=")


@pytest.mark.parametrize("token", ["", "wrong-token"])
def test_unpublish_rejects_invalid_csrf(client, unpublish_form, token):
    unpublish_form["csrf_token"] = token
    response = client.post("/solution/unpublish", data=unpublish_form)

    assert response.status_code == 400
    assert Solution.query.filter_by(revision=2).one().status == SolutionStatus.PUBLISHED


def test_unpublish_requires_revision(client, unpublish_form):
    del unpublish_form["solution_id"]
    response = client.post("/solution/unpublish", data=unpublish_form)

    assert response.status_code == 400
    assert Solution.query.filter_by(revision=2).one().status == SolutionStatus.PUBLISHED


def test_dashboard_shows_only_active_revisions(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Live revision" in response.data
    assert b"Draft revision" in response.data
    assert b"Old revision" not in response.data
    assert b'href="/solution/unpublish"' in response.data
    assert b'href="/archived"' in response.data


def test_archive_shows_only_unpublished_revisions(client):
    response = client.get("/archived")

    assert response.status_code == 200
    assert b"Old revision" in response.data
    assert b"Live revision" not in response.data
    assert b"Draft revision" not in response.data
    assert b"Unpublish</a>" not in response.data


def test_archive_shows_newest_revision_first(client):
    Solution.query.filter_by(revision=3).one().status = SolutionStatus.UNPUBLISHED
    db.session.commit()

    response = client.get("/archived")

    assert response.data.index(b"Draft revision") < response.data.index(b"Old revision")
