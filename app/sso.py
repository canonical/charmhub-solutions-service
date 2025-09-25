import functools

import flask
from django_openid_auth.teams import TeamsRequest, TeamsResponse
from urllib.parse import quote_plus
from flask_openid import OpenID

SSO_LOGIN_URL = "https://login.ubuntu.com"
DEFAULT_SSO_TEAM = "charmhub-solution-reviewers"


def init_sso(app: flask.Flask):
    open_id = OpenID(
        store_factory=lambda: None,
        safe_roots=[],
        extension_responses=[TeamsResponse],
    )

    SSO_TEAM = app.config.get("FLASK_OPENID_LAUNCHPAD_TEAM", DEFAULT_SSO_TEAM)

    @app.route("/login", methods=["GET", "POST"])
    @open_id.loginhandler
    def login():
        if "openid" in flask.session:
            return flask.redirect(open_id.get_next_url())

        teams_request = TeamsRequest(query_membership=[SSO_TEAM])
        return open_id.try_login(
            SSO_LOGIN_URL, ask_for=["email"], extensions=[teams_request]
        )

    @app.before_request
    def before_request():
        if flask.request.path == "/login":
            return
        if flask.request.path.startswith("/_status"):
            return
        if "openid" not in flask.session:
            return flask.redirect(
                "/login?next=" + quote_plus(flask.request.path)
            )


    @open_id.after_login
    def after_login(resp):
        if SSO_TEAM not in resp.extensions["lp"].is_member:
            flask.abort(403)

        flask.session["openid"] = {
            "identity_url": resp.identity_url,
            "email": resp.email,
        }

        return flask.redirect(open_id.get_next_url())


def dashboard_login_required(func):
    """
    Decorator that checks if a user is logged in, and redirects
    to login page if not.
    """

    @functools.wraps(func)
    def is_user_logged_in(*args, **kwargs):
        if "openid" not in flask.session:
            return flask.redirect("/login?next=" + flask.request.path)
        response = flask.make_response(func(*args, **kwargs))
        response.cache_control.private = True
        return response

    return is_user_logged_in
