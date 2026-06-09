from types import SimpleNamespace

from app.utils import serialize_public_solution


def test_public_serializer_excludes_private_fields():
    solution = SimpleNamespace(
        id=1,
        name="test-solution",
        hash="abc123",
        revision=1,
        status=SimpleNamespace(value="published"),
        visibility=SimpleNamespace(value="public"),
        title="Test Solution",
        summary="Summary",
        description="Description",
        terraform_modules=[],
        created=SimpleNamespace(isoformat=lambda: "2026-01-01T00:00:00"),
        last_updated=SimpleNamespace(
            isoformat=lambda: "2026-01-01T00:00:00"
        ),
        publisher=SimpleNamespace(
            publisher_id="publisher-id",
            display_name="Publisher",
            username="publisher",
        ),
        use_cases=[],
        platform=SimpleNamespace(value="kubernetes"),
        platform_version=[],
        platform_prerequisites=[],
        juju_versions=[],
        documentation_main=None,
        documentation_source=None,
        get_started_url=None,
        how_to_operate_url=None,
        architecture_explanation=None,
        submit_bug_url=None,
        community_discussion_url=None,
        icon=None,
        architecture_diagram_url=None,
        charms=[],
        maintainers=[],
        useful_links=[],
    )

    data = serialize_public_solution(solution)

    assert data["name"] == "test-solution"
    assert "creator" not in data
    assert "approved_by" not in data
