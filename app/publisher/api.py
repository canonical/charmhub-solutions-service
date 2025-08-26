from flask import Blueprint, jsonify, g, request
from app.publisher.logic import (
    get_solutions_by_lp_teams,
    create_empty_solution,
    get_solution_by_name,
    create_new_solution_revision,
    get_draft_solution_by_name,
    get_solution_by_name_and_rev,
    update_solution_metadata,
)
from app.public.logic import get_published_solution_by_name
from app.public.auth import login_required
from app.public.launchpad import get_user_teams

publisher_bp = Blueprint("publisher", __name__)


@publisher_bp.route("/solutions", methods=["GET"])
@login_required
def get_publisher_solutions():
    user = g.user
    teams = g.user["teams"]
    if not teams:
        teams = get_user_teams(user["username"])

    solutions = get_solutions_by_lp_teams(teams)
    return jsonify(solutions), 200


@publisher_bp.route("/solutions", methods=["POST"])
@login_required
def register_solution():
    user = g.user
    data = request.get_json()
    required_keys = ["name", "publisher", "description", "creator_email"]

    if not data or not all(key in data for key in required_keys):
        return (
            jsonify(
                {
                    "error": (
                        "Invalid request data, expected 'name', "
                        "'publisher', 'description', and "
                        "'creator_email'"
                    )
                }
            ),
            400,
        )

    teams = g.user["teams"]
    if not teams:
        teams = get_user_teams(user["username"])

    if data["publisher"] not in teams:
        return (
            jsonify({"error": "User must be a member of publishing group"}),
            404,
        )

    existing_solution = get_solution_by_name(data["name"])
    if existing_solution:
        return (
            jsonify({"error": "Solution with this name already exists"}),
            400,
        )

    res = create_empty_solution(
        name=data["name"],
        publisher=data["publisher"],
        description=data["description"],
        creator_email=data["creator_email"],
        mattermost_handle=data.get("mattermost_handle"),
        matrix_handle=data.get("matrix_handle"),
    )

    if not res:
        return jsonify({"error": "Failed to create solution"}), 500
    return jsonify(res), 201


@publisher_bp.route("/solutions/<string:name>/<int:rev>", methods=["GET"])
@login_required
def get_solution_revision(name, rev):
    solution = get_solution_by_name_and_rev(name, rev)

    if not solution:
        return jsonify({"error": "Solution revision not found"}), 404

    teams = g.user["teams"]

    if solution["publisher"]["username"] not in teams:
        return jsonify({"error": "Solution revision not found"}), 404

    return jsonify(solution), 200


@publisher_bp.route("/solutions/<string:name>/", methods=["POST"])
@login_required
def create_solution_revision(name):
    user = g.user
    data = request.get_json()
    required_keys = ["creator_email"]

    if not data or not all(key in data for key in required_keys):
        return (
            jsonify(
                {"error": "Invalid request data, expected 'creator_email'"}
            ),
            400,
        )

    current_solution = get_published_solution_by_name(name)

    if not current_solution:
        return jsonify({"error": "Solution not found"}), 404

    teams = g.user["teams"]
    if current_solution["publisher"]["username"] not in teams:
        return jsonify({"error": "Solution not found"}), 404

    draft_solution = get_draft_solution_by_name(name)

    if draft_solution:
        return jsonify({"error": "Draft already exists"}), 400

    solution = create_new_solution_revision(
        name=name,
        creator_email=data["creator_email"],
        mattermost_handle=data.get("mattermost_handle"),
        matrix_handle=data.get("matrix_handle"),
    )

    return jsonify(solution), 200


@publisher_bp.route("/solutions/<string:name>/<int:rev>", methods=["PATCH"])
@login_required
def update_solution_revision(name, rev):
    user = g.user
    solution = get_solution_by_name_and_rev(name, rev)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404

    teams = g.user["teams"]
    if not teams:
        teams = get_user_teams(user["username"])

    if solution["publisher"]["username"] not in teams:
        return jsonify({"error": "Solution not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    updated_solution = update_solution_metadata(name, rev, data)

    if not updated_solution:
        return jsonify({"error": "Failed to update solution"}), 500

    return jsonify(updated_solution), 200
