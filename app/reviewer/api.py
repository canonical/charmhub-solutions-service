"""
### TO DO ###
These endpoints need to be wrapped in auth
Reviewers must be part of "charmhub-solution-reviewers" launchpad team
"""

from flask import Blueprint, jsonify, g, redirect, url_for, current_app
from app.reviewer.logic import (
    approve_solution_name,
    approve_solution_metadata,
    unpublish_solution,
    republish_solution,
)

# from app.public.auth import login_required

reviewer_bp = Blueprint("reviewer", __name__)


@reviewer_bp.route("/<string:name>/approve-name", methods=["GET"])
# @login_required
def approve_name(name):
    # if "charmhub-solution-reviewers" not in g.user["teams"]:
    #     return jsonify({"error": "Forbidden"}), 403
    solution = approve_solution_name(name)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    if current_app.config.get("TESTING"):
        return jsonify(solution)
    return redirect(url_for("dashboard.dashboard"))


@reviewer_bp.route("/<string:name>/approve-metadata", methods=["GET"])
# @login_required
def approve_metadata(name):
    # if "charmhub-solution-reviewers" not in g.user["teams"]:
    #     return jsonify({"error": "Forbidden"}), 403
    solution = approve_solution_metadata(name)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    if current_app.config.get("TESTING"):
        return jsonify(solution)
    return redirect(url_for("dashboard.dashboard"))


@reviewer_bp.route("/<string:name>/unpublish", methods=["GET"])
# @login_required
def unpublish(name):
    # if "charmhub-solution-reviewers" not in g.user["teams"]:
    #     return jsonify({"error": "Forbidden"}), 403
    solution = unpublish_solution(name)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    if current_app.config.get("TESTING"):
        return jsonify(solution)
    return redirect(url_for("dashboard.dashboard"))


@reviewer_bp.route("/<string:name>/republish", methods=["GET"])
# @login_required
def republish(name):
    # if "charmhub-solution-reviewers" not in g.user["teams"]:
    #     return jsonify({"error": "Forbidden"}), 403
    solution = republish_solution(name)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    if current_app.config.get("TESTING"):
        return jsonify(solution)
    return redirect(url_for("dashboard.dashboard"))
