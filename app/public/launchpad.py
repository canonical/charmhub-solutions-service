import requests
import functools
import time 

LAUNCHPAD_URL = "https://api.launchpad.net/1.0/"

def time_cache(max_age, maxsize=128):
    """Least-recently-used cache decorator with time-based cache invalidation.

    Args:
        max_age: Time to live for cached results (in seconds).
        maxsize: Maximum cache size (see `functools.lru_cache`).
    """
    def _decorator(fn):
        @functools.lru_cache(maxsize=maxsize)
        def _new(*args, __time_salt, **kwargs):
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        def _wrapped(*args, **kwargs):
            # this is a trick to "turn" the lru_cache into a time-based cache
            return _new(*args, **kwargs, __time_salt=int(time.time() / max_age))

        return _wrapped

    return _decorator


@time_cache(max_age=3600)
def get_user_teams(username):
    url = f"{LAUNCHPAD_URL}/~{username}/super_teams"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch teams for user {username}: {response.text}"
        )

    teams = response.json()["entries"]
    return [team["name"] for team in teams]


def get_launchpad_team(team_name):
    url = f"{LAUNCHPAD_URL}/~{team_name}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return None

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team {team_name}: "
                f"{response.status_code} {response.text}"
            )

        team_data = response.json()

        return {
            "name": team_data.get("name"),
            "display_name": team_data.get("display_name"),
            "web_link": team_data.get("web_link"),
        }
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to Launchpad API: {str(e)}")
