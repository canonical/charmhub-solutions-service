from flask import Blueprint, request, jsonify, g
from app.models import Publisher
from app.public.logic import (
    get_all_published_solutions,
    get_published_solution_by_name,
    get_published_solution_by_hash,
    search_published_solutions,
)
from app.public.auth import login_required, verify_signature
from app.public.launchpad import get_user_teams
import os
import time
import jwt

public_bp = Blueprint("public", __name__)

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

    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRATION,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token})


@public_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    teams = g.user.get("teams", [])
    publishers = Publisher.query.filter(Publisher.username.in_(teams)).all()
    g.user["is_publisher"] = len(publishers) > 0
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
    solution = get_published_solution_by_hash(uuid)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    return jsonify(solution), 200
