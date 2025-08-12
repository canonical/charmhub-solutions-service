from flask import (
    Blueprint,
    render_template,
    jsonify,
    redirect,
    url_for,
    current_app,
)
from app.models import Solution, SolutionStatus
from sqlalchemy.orm import joinedload
from app.reviewer.logic import (
    approve_solution_name,
    approve_solution_metadata,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/_status/check")
def status_check():
    """Health check endpoint."""
    return "OK", 200


@dashboard_bp.route("/")
def dashboard():
    solutions_query = Solution.query.options(
        joinedload(Solution.publisher)
    ).all()

    published_solutions = []
    pending_metadata_review_solutions = []
    pending_name_review_solutions = []

    for solution in solutions_query:
        solution_data = {
            "name": solution.name,
            "title": solution.title,
            "status": solution.status.value,
            "publisher_username": solution.publisher.username,
            "publisher_display_name": solution.publisher.display_name,
            "hash": solution.hash,
        }
        if solution.status == SolutionStatus.PUBLISHED:
            published_solutions.append(solution_data)
        elif solution.status == SolutionStatus.PENDING_METADATA_REVIEW:
            pending_metadata_review_solutions.append(solution_data)
        elif solution.status == SolutionStatus.PENDING_NAME_REVIEW:
            pending_name_review_solutions.append(solution_data)

    return render_template(
        "dashboard.html",
        published_solutions=published_solutions,
        pending_metadata_review_solutions=pending_metadata_review_solutions,
        pending_name_review_solutions=pending_name_review_solutions,
    )


@dashboard_bp.route("/<string:name>/approve-name", methods=["GET"])
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


@dashboard_bp.route("/<string:name>/approve-metadata", methods=["GET"])
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
