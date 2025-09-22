import pytest
from unittest.mock import patch
from app.public.store_api import get_publisher_details
from app.exceptions import ValidationError


class TestGetPublisherDetails:
    @patch("app.public.store_api.device_gateway")
    def test_publisher_with_packages(self, mock_gateway):
        mock_response = {
            "results": [
                {
                    "result": {
                        "publisher": {
                            "id": "abc123hash",
                            "username": "test-publisher",
                            "display-name": "Test Publisher",
                        }
                    }
                }
            ]
        }
        mock_gateway.find.return_value = mock_response

        result = get_publisher_details("test-publisher")

        assert result == {
            "id": "abc123hash",
            "username": "test-publisher",
            "display_name": "Test Publisher",
        }
        mock_gateway.find.assert_called_once_with(
            publisher="test-publisher", fields=["result.publisher"]
        )

    @patch("app.public.store_api.device_gateway")
    def test_publisher_without_packages(self, mock_gateway):
        mock_response = {"results": []}
        mock_gateway.find.return_value = mock_response

        with pytest.raises(ValidationError) as exception_info:
            get_publisher_details("new-publisher")

        errors = exception_info.value.errors
        assert len(errors) == 1
        assert errors[0]["code"] == "invalid-publisher"
        assert errors[0]["message"] == "Publisher not found"

    @patch("app.public.store_api.device_gateway")
    def test_device_gateway_error(self, mock_gateway):
        mock_gateway.find.side_effect = ConnectionError("Network error")

        with pytest.raises(ValidationError) as exception_info:
            get_publisher_details("error-publisher")

        errors = exception_info.value.errors
        assert len(errors) == 1
        assert errors[0]["code"] == "invalid-publisher"
        assert errors[0]["message"] == "Publisher not found"

    @patch("app.public.store_api.device_gateway")
    def test_incorrect_response(self, mock_gateway):
        mock_response = {
            "results": [
                {
                    "result": {
                        "publisher": {
                            "id": "abc123",
                        }
                    }
                }
            ]
        }
        mock_gateway.find.return_value = mock_response

        result = get_publisher_details("test-publisher")

        assert result == {
            "id": "abc123",
            "username": None,
            "display_name": None,
        }
