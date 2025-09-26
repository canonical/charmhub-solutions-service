from flask import Blueprint, jsonify, g, request
from app.publisher.logic import (
    get_solutions_by_lp_teams,
    create_new_solution_revision,
    get_draft_solution_by_name,
    get_solution_by_name_and_rev,
    update_solution_metadata,
    register_solution_package,
    find_or_create_creator,
)
from app.public.logic import get_published_solution_by_name
from app.public.auth import login_required
from app.public.launchpad import get_user_teams
from app.exceptions import ValidationError

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
    data = request.get_json()
    required_keys = ["name", "publisher", "summary", "creator_email"]

    if not data or not all(key in data for key in required_keys):
        return (
            jsonify(
                {
                    "error": (
                        "Invalid request data, expected 'name', "
                        "'publisher', 'summary', and "
                        "'creator_email'"
                    )
                }
            ),
            400,
        )

    teams = g.user["teams"]
    if not teams:
        teams = get_user_teams(g.user["username"])

    try:
        creator = find_or_create_creator(
            data["creator_email"],
            data.get("mattermost_handle"),
            data.get("matrix_handle"),
        )

        solution = register_solution_package(
            teams=teams,
            name=data["name"],
            publisher=data["publisher"],
            summary=data["summary"],
            creator=creator,
            title=data.get("title"),
            platform=data.get("platform", "kubernetes"),
        )

        return jsonify(solution), 201

    except ValidationError as e:
        return jsonify({"error-list": e.errors}), 400


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

    creator = find_or_create_creator(
        data["creator_email"],
        data.get("mattermost_handle"),
        data.get("matrix_handle"),
    )

    solution = create_new_solution_revision(
        name=name,
        creator=creator,
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
