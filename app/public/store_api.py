from canonicalwebteam.store_api.devicegw import DeviceGW
import logging
from app.exceptions import ValidationError

device_gateway = DeviceGW("charm")


def get_publisher_details(publisher_username):
    """
    Get publisher details from device gateway
    - similar logic to how we do this in charmhub
    """
    try:
        response = device_gateway.find(
            publisher=publisher_username, fields=["result.publisher"]
        )

        if response.get("results") and len(response["results"]) > 0:
            publisher_data = response["results"][0]["result"]["publisher"]

            return {
                "id": publisher_data.get("id"),
                "username": publisher_data.get("username"),
                "display_name": publisher_data.get("display-name")
                or publisher_data.get("display_name"),
            }
        else:
            raise ValidationError(
                [
                    {
                        "code": "invalid-publisher",
                        "message": "Publisher not found",
                    }
                ]
            )

    except ValidationError:
        raise
    except Exception as e:
        logging.error(
            f"Failed to fetch publisher details for {publisher_username}: {e}"
        )
        raise ValidationError(
            [{"code": "invalid-publisher", "message": "Publisher not found"}]
        )
