from flask import Blueprint, request, jsonify
from app.public.logic import (
    get_all_published_solutions,
    get_published_solution_by_name,
    search_published_solutions,
)
from app.public.auth import login_required, verify_signature
from app.public.launchpad import get_user_teams
import os
import time
import jwt

public_bp = Blueprint("public", __name__)

JWT_EXPIRATION = 86400 # 24 hours
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
        "exp": int(time.time()) + JWT_EXPIRATION
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token})

@public_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    return jsonify({
        "username": payload["sub"],
        "teams": payload.get("teams", [])
    }), 200

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
