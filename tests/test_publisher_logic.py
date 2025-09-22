import pytest
from unittest.mock import Mock, patch
from app.publisher.logic import (
    find_or_create_creator,
    register_solution_package,
    create_empty_solution
)
from app.models import Creator
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
            "new@example.com", "mattermost_handle", "matrix_handle"
        )

        mock_creator_class.assert_called_once_with(
            email="new@example.com",
            mattermost_handle="mattermost_handle",
            matrix_handle="matrix_handle",
        )
        mock_session.add.assert_called_once_with(new_creator)
        mock_session.flush.assert_called_once()
        assert result == new_creator

    @patch("app.publisher.logic.db.session")
    def test_update_existing_creator_handles(self, mock_session):
        existing_creator = Mock(spec=Creator)
        existing_creator.email = "test@example.com"
        existing_creator.mattermost_handle = None
        existing_creator.matrix_handle = None
        mock_session.query().filter().first.return_value = existing_creator

        result = find_or_create_creator(
            "test@example.com", "new_mattermost", "new_matrix"
        )

        assert existing_creator.mattermost_handle == "new_mattermost"
        assert existing_creator.matrix_handle == "new_matrix"
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
