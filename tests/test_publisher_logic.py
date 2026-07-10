import pytest
from unittest.mock import Mock, patch
from app.publisher.logic import (
    find_or_create_creator,
    register_solution_package,
    create_empty_solution,
    validate_solution_metadata,
    validate_solution_categories,
    update_solution_metadata,
)
from app.models import Creator, SolutionStatus
from app.exceptions import ValidationError


class TestFindOrCreateCreator:
    @patch("app.publisher.logic.db.session")
    def test_find_existing_creator(self, mock_session):
        existing_creator = Mock(spec=Creator)
        existing_creator.email = "test@example.com"
        mock_session.query().filter().first.return_value = existing_creator

        result = find_or_create_creator("test@example.com")

        assert result == existing_creator
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()

    @patch("app.publisher.logic.db.session")
    @patch("app.publisher.logic.Creator")
    def test_create_new_creator(self, mock_creator_class, mock_session):
        mock_session.query().filter().first.return_value = None
        new_creator = Mock(spec=Creator)
        mock_creator_class.return_value = new_creator

        result = find_or_create_creator(
            "new@example.com", "mattermost_handle"
        )

        mock_creator_class.assert_called_once_with(
            email="new@example.com",
            mattermost_handle="mattermost_handle",
        )
        mock_session.add.assert_called_once_with(new_creator)
        mock_session.flush.assert_called_once()
        assert result == new_creator

    @patch("app.publisher.logic.db.session")
    def test_update_existing_creator_handles(self, mock_session):
        existing_creator = Mock(spec=Creator)
        existing_creator.email = "test@example.com"
        existing_creator.mattermost_handle = None
        mock_session.query().filter().first.return_value = existing_creator

        result = find_or_create_creator(
            "test@example.com", "new_mattermost"
        )

        assert existing_creator.mattermost_handle == "new_mattermost"
        assert result == existing_creator


class TestRegisterSolutionPackage:
    def test_invalid_name_validation(self):
        mock_creator = Mock(id=1)
        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["test-team"],
                name="Invalid_Name!",
                publisher="test-team",
                summary="Test summary",
                creator=mock_creator,
            )

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert errors[0]["code"] == "invalid-name"
        assert (
            "lowercase letters, numbers, and hyphens" in errors[0]["message"]
        )

    def test_no_letters_validation(self):
        mock_creator = Mock(id=1)
        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["test-team"],
                name="123-456",
                publisher="test-team",
                summary="Test summary",
                creator=mock_creator,
            )

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert errors[0]["code"] == "invalid-name"

    def test_name_max_length_validation(self):
        mock_creator = Mock(id=1)
        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["test-team"],
                name="a" * 41,
                publisher="test-team",
                summary="Test summary",
                creator=mock_creator,
            )

        assert exc_info.value.errors[0]["code"] == "invalid-name"

    def test_summary_max_length_validation(self):
        mock_creator = Mock(id=1)
        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["test-team"],
                name="valid-name",
                publisher="test-team",
                summary="a" * 501,
                creator=mock_creator,
            )

        assert exc_info.value.errors[0]["code"] == "invalid-summary"

    def test_invalid_platform_validation(self):
        mock_creator = Mock(id=1)
        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["test-team"],
                name="valid-name",
                publisher="test-team",
                summary="Test summary",
                creator=mock_creator,
                platform="invalid-platform",
            )

        assert exc_info.value.errors[0]["code"] == "invalid-platform"

    def test_metadata_title_max_length_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata({"title": "a" * 31})

        assert exc_info.value.errors[0]["code"] == "invalid-title"
        assert exc_info.value.errors[0]["field"] == "Title"

    def test_metadata_description_max_length_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata({"description": "a" * 2001})

        assert exc_info.value.errors[0]["code"] == "invalid-description"

    def test_metadata_architecture_explanation_max_length_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {"architecture_explanation": "a" * 2001}
            )

        assert (
            exc_info.value.errors[0]["code"]
            == "invalid-architecture-explanation"
        )

    def test_metadata_platform_version_count_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata({"platform_version": []})

        assert exc_info.value.errors[0]["code"] == "invalid-platform-version"

        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {"platform_version": ["1", "2", "3", "4"]}
            )

        assert exc_info.value.errors[0]["code"] == "invalid-platform-version"

    def test_metadata_juju_versions_count_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata({"juju_versions": []})

        assert exc_info.value.errors[0]["code"] == "invalid-juju-versions"

        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata({"juju_versions": ["1", "2", "3", "4"]})

        assert exc_info.value.errors[0]["code"] == "invalid-juju-versions"

    def test_metadata_use_case_title_length_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {
                    "use_cases": [
                        {"title": "a" * 61, "description": "valid"}
                    ]
                }
            )

        assert exc_info.value.errors[0]["code"] == "invalid-use-cases"

    def test_metadata_use_case_description_length_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {
                    "use_cases": [
                        {"title": "valid", "description": "a" * 501}
                    ]
                }
            )

        assert exc_info.value.errors[0]["code"] == "invalid-use-cases"

    def test_metadata_useful_link_title_length_validation(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {
                    "useful_links": [
                        {
                            "title": "a" * 31,
                            "url": "https://example.com",
                        }
                    ]
                }
            )

        assert exc_info.value.errors[0]["code"] == "invalid-useful-links"

    def test_metadata_categories_required(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {"title": "Valid", "summary": "ok", "categories": []}
            )

        assert exc_info.value.errors[0]["code"] == "invalid-categories"

    def test_metadata_categories_too_many(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_solution_metadata(
                {"categories": ["ai-ml", "storage", "cloud"]}
            )

        assert exc_info.value.errors[0]["code"] == "invalid-categories"

    def test_metadata_valid_categories(self):
        validate_solution_metadata(
            {
                "title": "Valid",
                "summary": "ok",
                "categories": ["ai-ml", "storage"],
            }
        )

    def test_validate_solution_categories_count(self):
        assert validate_solution_categories(["ai-ml"]) is True
        assert validate_solution_categories(["ai-ml", "storage"]) is True
        assert validate_solution_categories([]) is False
        assert validate_solution_categories(["a", "b", "c"]) is False
        assert validate_solution_categories(None) is False

    @patch("app.publisher.logic.get_solution_by_name")
    def test_already_exists_validation(self, mock_get_solution):
        mock_get_solution.return_value = {"name": "existing-solution"}
        mock_creator = Mock(id=1)

        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["test-team"],
                name="existing-solution",
                publisher="test-team",
                summary="Test summary",
                creator=mock_creator,
            )

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert errors[0]["code"] == "already-registered"

    @patch("app.publisher.logic.get_solution_by_name")
    def test_access_denied_validation(self, mock_get_solution):
        mock_get_solution.return_value = None
        mock_creator = Mock(id=1)

        with pytest.raises(ValidationError) as exc_info:
            register_solution_package(
                teams=["user-team"],
                name="valid-name",
                publisher="different-team",
                summary="Test summary",
                creator=mock_creator,
            )

        errors = exc_info.value.errors
        assert len(errors) == 1
        assert errors[0]["code"] == "access-denied"

    @patch("app.publisher.logic.create_empty_solution")
    @patch("app.publisher.logic.get_solution_by_name")
    def test_successful_registration(
        self, mock_get_solution, mock_create_solution
    ):
        mock_get_solution.return_value = None
        mock_creator = Mock(id=1)
        mock_create_solution.return_value = {"name": "test-solution"}

        result = register_solution_package(
            teams=["test-team"],
            name="test-solution",
            publisher="test-team",
            summary="Test summary",
            creator=mock_creator,
        )

        mock_create_solution.assert_called_once()
        assert result == {"name": "test-solution"}


class TestUpdateSolutionMetadata:
    @patch("app.publisher.logic.update_published_solution")
    @patch("app.publisher.logic.update_draft_solution")
    @patch("app.publisher.logic.find_draft_solution_by_name")
    @patch("app.publisher.logic.validate_solution_metadata")
    @patch("app.publisher.logic.db.session")
    def test_published_update_reuses_existing_draft(
        self,
        mock_session,
        mock_validate_solution_metadata,
        mock_find_draft_solution_by_name,
        mock_update_draft_solution,
        mock_update_published_solution,
    ):
        published_solution = Mock(status=SolutionStatus.PUBLISHED)
        draft_solution = Mock(status=SolutionStatus.DRAFT)
        metadata = {"title": "Updated Title"}

        mock_session.query().filter().first.return_value = published_solution
        mock_find_draft_solution_by_name.return_value = draft_solution
        mock_update_draft_solution.return_value = {
            "revision": 2,
            "status": "published",
        }

        result = update_solution_metadata(
            "test-solution",
            1,
            metadata,
            submit_for_review=True,
        )

        assert result == {"revision": 2, "status": "published"}
        mock_validate_solution_metadata.assert_called_once_with(metadata)
        mock_update_draft_solution.assert_called_once_with(
            draft_solution,
            metadata,
            submit_for_review=True,
        )
        mock_update_published_solution.assert_not_called()

    @patch("app.publisher.logic.update_draft_solution")
    @patch("app.publisher.logic.db.session")
    def test_submit_keeps_existing_categories_when_omitted(
        self,
        mock_session,
        mock_update_draft_solution,
    ):
        solution = Mock(
            status=SolutionStatus.DRAFT,
            revision=1,
            categories=["ai-ml"],
        )
        mock_session.query().filter().first.return_value = solution
        mock_update_draft_solution.return_value = {"revision": 1}
        metadata = {"title": "Valid", "summary": "ok"}

        result = update_solution_metadata(
            "test-solution", 1, metadata, submit_for_review=True
        )

        assert result == {"revision": 1}
        assert metadata["categories"] == ["ai-ml"]


class TestTransactionSafety:
    @patch("app.publisher.logic.get_publisher_details")
    @patch("app.publisher.logic.db.session")
    def test_rollback_on_exception(self, mock_session, mock_get_publisher_details):
        mock_creator = Mock(id=1)
        mock_session.query().filter().first.return_value = None

        mock_get_publisher_details.return_value = {
            "id": "test-publisher-id",
            "username": "test-publisher",
            "display_name": "Test Publisher"
        }

        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            create_empty_solution(
                name="test-solution",
                publisher="test-publisher",
                summary="Test summary",
                creator=mock_creator,
            )

        mock_session.rollback.assert_called_once()
