from flask import Blueprint, request, jsonify, g
from app.public.logic import (
    get_all_published_solutions,
    get_published_solution_by_name,
    get_solution_by_hash,
    get_solution_by_name_and_rev,
    search_published_solutions,
    create_new_solution_revision,
    get_draft_solution_by_name,
)
from app.public.auth import login_required, verify_signature
from app.public.launchpad import get_user_teams
from app.public.publisher import publisher_bp
import os
import time
import jwt

public_bp = Blueprint("public", __name__)

public_bp.register_blueprint(publisher_bp, url_prefix="/publisher")

JWT_EXPIRATION = 86400  # 24 hours
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]


@public_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    timestamp = data.get("timestamp")
    signature = data.get("signature")

    if not all([username, timestamp, signature]):
        return jsonify({"error": "Missing fields"}), 400

    if not verify_signature(username, timestamp, signature):
        return jsonify({"error": "Invalid or expired signature"}), 403

    # Fetch user teams from Launchpad
    try:
        teams = get_user_teams(username)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    print(teams)

    payload = {
        "sub": username,
        "teams": teams,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRATION,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token})


@public_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    return jsonify({"user": g.user}), 200


@public_bp.route("/solutions", methods=["GET"])
def list_published_solutions():
    solutions = get_all_published_solutions()
    return jsonify(solutions), 200


@public_bp.route("/solutions/<string:name>", methods=["GET"])
def get_solution(name):
    solution = get_published_solution_by_name(name)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    return jsonify(solution), 200


@public_bp.route("/solutions/search", methods=["GET"])
def search_solutions():
    query = request.args.get("q", "")
    results = search_published_solutions(query)
    return jsonify(results), 200


@public_bp.route("/solutions/preview/<string:uuid>", methods=["GET"])
def get_solution_preview(uuid):
    solution = get_solution_by_hash(uuid)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    return jsonify(solution), 200


@login_required
@public_bp.route("/solutions/<string:name>/<int:rev>", methods=["GET"])
def get_solution_revision(name, rev):
    solution = get_solution_by_name_and_rev(name, rev)

    if not solution:
        return jsonify({"error": "Solution revision not found"}), 404

    teams = g.user["teams"]

    if solution["publisher"] not in teams:
        return jsonify({"error": "Solution revision not found"}), 404

    return jsonify(solution), 200


@public_bp.route("/solutions/<string:name>/", methods=["POST"])
@login_required
def create_solution_revision(name):
    current_solution = get_published_solution_by_name(name)

    if not current_solution:
        return jsonify({"error": "Solution not found"}), 404

    teams = g.user["teams"]
    if current_solution["publisher"]['username'] not in teams:
        return jsonify({"error": "Solution not found"}), 404

    draft_solution = get_draft_solution_by_name(name)

    if draft_solution:
        return jsonify({"error": "Draft already exists"}), 400

    solution = create_new_solution_revision(name)

    return jsonify(solution), 200
