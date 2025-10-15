from flask import (
    Blueprint,
    render_template,
    jsonify,
    redirect,
    url_for,
    current_app,
    session,
)
from app.models import Solution, SolutionStatus
from sqlalchemy.orm import joinedload
from app.reviewer.logic import (
    approve_solution_name,
    approve_solution_metadata,
)
from app.sso import dashboard_login_required

dashboard_bp = Blueprint("dashboard", __name__)


def get_reviewer_id():
    if "openid" not in session:
        return None
    return session["openid"].get("email", "")


@dashboard_bp.route("/_status/check")
def status_check():
    """Health check endpoint."""
    return "OK", 200


@dashboard_bp.route("/")
@dashboard_login_required
def dashboard():
    solutions_query = Solution.query.options(
        joinedload(Solution.publisher), joinedload(Solution.creator)
    ).all()

    published_solutions = []
    pending_metadata_review_solutions = []
    pending_name_review_solutions = []

    for solution in solutions_query:
        solution_data = {
            "name": solution.name,
            "title": solution.title,
            "revision": solution.revision,
            "status": solution.status.value,
            "publisher_username": solution.publisher.username,
            "publisher_display_name": solution.publisher.display_name,
            "creator_mattermost": solution.creator.mattermost_handle,
            "hash": solution.hash,
            "last_updated": solution.last_updated,
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
@dashboard_login_required
def approve_name(name):
    reviewer_id = get_reviewer_id()
    if not reviewer_id:
        return jsonify({"error": "Reviewer ID not found in session"}), 400
    solution = approve_solution_name(name, reviewer_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    if current_app.config.get("TESTING"):
        return jsonify(solution)
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/<string:name>/approve-metadata", methods=["GET"])
@dashboard_login_required
def approve_metadata(name):
    reviewer_id = get_reviewer_id()
    if not reviewer_id:
        return jsonify({"error": "Reviewer ID not found in session"}), 400
    solution = approve_solution_metadata(name, reviewer_id)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    if current_app.config.get("TESTING"):
        return jsonify(solution)
    return redirect(url_for("dashboard.dashboard"))
