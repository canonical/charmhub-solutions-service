
from flask import Blueprint, jsonify, g, request
from app.public.logic import (
    get_solutions_by_lp_teams,
    create_empty_solution,
    get_solution_by_name
)
from app.public.auth import login_required
from app.public.launchpad import get_user_teams
publisher_bp = Blueprint("publisher", __name__)

@publisher_bp.route("/solutions", methods=["GET"])
@login_required
def get_publisher_solutions():
    user = g.user
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    teams = g.user["teams"]
    if not teams:
        teams = get_user_teams(user["username"])

    solutions = get_solutions_by_lp_teams(teams)
    return jsonify(solutions), 200

@publisher_bp.route("/solutions", methods=["POST"])
@login_required
def register_solution():
    user = g.user
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    if not data or not all(key in data for key in ["name", "publisher", "description"]):
        return jsonify({"error": f"Invalid request data, expected 'name', 'publisher', and 'description'"}), 400

    teams = g.user["teams"]
    if not teams:
        teams = get_user_teams(user["username"])

    if data["publisher"] not in teams:
        return jsonify({"error": "User must be a member of publishing group"}), 404

    existing_solution = get_solution_by_name(data["name"])
    if existing_solution:
        return jsonify({"error": "Solution with this name already exists"}), 400

    res = create_empty_solution(
        name=data["name"],
        publisher=data["publisher"],
        description=data["description"],
        created_by=user["username"]
    )

    if not res:
        return jsonify({"error": "Failed to create solution"}), 500
    return jsonify(res), 201
