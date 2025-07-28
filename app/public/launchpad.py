import requests
LAUNCHPAD_URL = "https://api.launchpad.net/1.0/"


def get_user_teams(username):
    url = f"{LAUNCHPAD_URL}/~{username}/super_teams"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch teams for user {username}: {response.text}")

    teams = response.json()["entries"]
    return [team['name'] for team in teams]
