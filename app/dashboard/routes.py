import secrets

from flask import (
    Blueprint,
    render_template,
    jsonify,
    redirect,
    url_for,
    current_app,
    session,
    request,
    flash,
    abort,
)
from app.models import (
    Solution,
    SolutionStatus,
    Publisher,
    Visibility,
)
from app.extensions import db
from sqlalchemy.orm import joinedload
from app.reviewer.logic import (
    approve_solution_name,
    approve_solution_metadata,
)
from app.sso import dashboard_login_required
from app.public.launchpad import get_launchpad_team
from app.public.store_api import get_publisher_details
from app.exceptions import ValidationError

dashboard_bp = Blueprint("dashboard", __name__)


def get_reviewer_id():
    if "openid" not in session:
        return None
    return session["openid"].get("email", "")


def validate_publisher(username):
    team_data = get_launchpad_team(username)
    if team_data is None:
        return None, None, f"Launchpad team '{username}' does not exist"

    # get publisher ID from Store API (if they have pblished charms)
    try:
        store_data = get_publisher_details(username)
        publisher_id = store_data.get("id")
    except ValidationError:
        publisher_id = team_data["name"]
    except Exception:
        publisher_id = team_data["name"]

    # check if publisher already exists
    existing_by_id = Publisher.query.filter_by(
        publisher_id=publisher_id
    ).first()

    existing_by_username = Publisher.query.filter_by(
        username=username
    ).first()

    if existing_by_id or existing_by_username:
        return (
            team_data,
            publisher_id,
            f"Publisher '{username}' already exists in the database",
        )

    return team_data, publisher_id, None


@dashboard_bp.route("/_status/check")
def status_check():
    """Health check endpoint."""
    return "OK", 200


@dashboard_bp.route("/", defaults={"archived": False})
@dashboard_bp.route(
    "/archived", endpoint="archived", defaults={"archived": True}
)
@dashboard_login_required
def dashboard(archived):
    query = Solution.query.options(
        joinedload(Solution.publisher), joinedload(Solution.creator)
    )
    query = query.filter(
        Solution.status == SolutionStatus.UNPUBLISHED
        if archived
        else Solution.status != SolutionStatus.UNPUBLISHED
    )
    solutions_query = query.order_by(
        Solution.name, Solution.revision.desc()
    ).all()

    published_solutions = []
    pending_metadata_review_solutions = []
    draft_solutions = []
    pending_name_review_solutions = []
    unpublished_solutions = []

    for solution in solutions_query:
        solution_data = {
            "name": solution.name,
            "title": solution.title,
            "revision": solution.revision,
            "status": solution.status.value,
            "visibility": solution.visibility.value,
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
        elif solution.status == SolutionStatus.DRAFT:
            draft_solutions.append(solution_data)
        elif solution.status == SolutionStatus.PENDING_NAME_REVIEW:
            pending_name_review_solutions.append(solution_data)
        elif solution.status == SolutionStatus.UNPUBLISHED:
            unpublished_solutions.append(solution_data)

    if archived:
        return render_template(
            "archived.html",
            unpublished_solutions=unpublished_solutions,
        )
    return render_template(
        "dashboard.html",
        published_solutions=published_solutions,
        pending_metadata_review_solutions=pending_metadata_review_solutions,
        draft_solutions=draft_solutions,
        pending_name_review_solutions=pending_name_review_solutions,
    )


@dashboard_bp.route("/<string:name>/review", methods=["GET"])
@dashboard_login_required
def review_solution(name):
    solution = (
        Solution.query.filter_by(name=name)
        .order_by(Solution.revision.desc())
        .first()
    )

    if not solution:
        flash("Solution not found", "negative")
        return redirect(url_for("dashboard.dashboard"))

    if solution.status not in [
        SolutionStatus.PENDING_NAME_REVIEW,
        SolutionStatus.PENDING_METADATA_REVIEW,
    ]:
        flash("This solution is not pending review", "information")
        return redirect(url_for("dashboard.dashboard"))

    return render_template("review_solution.html", solution=solution)


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


@dashboard_bp.route(
    "/<string:name>/unpublish",
    methods=["GET", "POST"],
)
@dashboard_login_required
def unpublish_solution(name):
    reviewer_id = get_reviewer_id()
    if not reviewer_id:
        abort(403)

    if request.method == "POST":
        token = session.get("solution_action_csrf_token")
        if not token or not secrets.compare_digest(
            token.encode(), request.form.get("csrf_token", "").encode()
        ):
            abort(400, description="Invalid CSRF token")

    query = Solution.query.filter_by(
        name=name, status=SolutionStatus.PUBLISHED
    )
    if request.method == "POST":
        solution_id = request.form.get("solution_id", type=int)
        if solution_id is None:
            abort(400, description="Solution revision is required")
        query = query.filter_by(id=solution_id).with_for_update()
    solution = query.order_by(Solution.revision.desc()).first()
    if not solution:
        if request.method == "POST":
            abort(409, description="This revision is no longer published")
        abort(404)

    if request.method == "GET":
        if "solution_action_csrf_token" not in session:
            session["solution_action_csrf_token"] = secrets.token_hex(32)
        return render_template(
            "confirm_unpublish.html",
            solution=solution,
            csrf_token=session["solution_action_csrf_token"],
        )

    try:
        solution.status = SolutionStatus.UNPUBLISHED
        solution.visibility = Visibility.PRIVATE
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    current_app.logger.info(
        "Reviewer %s unpublished solution %s revision %s",
        reviewer_id, name, solution.revision,
    )
    flash(f"Solution '{name}' unpublished successfully", "positive")
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/create-publisher", methods=["GET"])
@dashboard_login_required
def show_create_publisher():
    publishers = Publisher.query.order_by(Publisher.username).all()
    return render_template("create_publisher.html", publishers=publishers)


@dashboard_bp.route("/validate-launchpad-team")
@dashboard_login_required
def validate_launchpad_team():
    username = request.args.get("username", "").strip()

    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        team_data, publisher_id, error = validate_publisher(username)

        if team_data is None:
            return jsonify({"exists": False, "message": error}), 404

        if error:
            return (
                jsonify(
                    {
                        "exists": True,
                        "already_created": True,
                        "message": error
                    }
                ),
                409,
            )

        return jsonify(
            {
                "exists": True,
                "already_created": False,
                "name": team_data["name"],
                "display_name": team_data["display_name"],
                "web_link": team_data["web_link"],
                "publisher_id": publisher_id,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/create-publisher", methods=["POST"])
@dashboard_login_required
def create_publisher():
    username = request.form.get("username", "").strip()

    if not username:
        flash("Username is required", "negative")
        return redirect(url_for("dashboard.show_create_publisher"))

    try:
        team_data, publisher_id, error = validate_publisher(username)

        if team_data is None or error:
            flash(error, "negative")
            return redirect(url_for("dashboard.show_create_publisher"))

        display_name = team_data["display_name"]

    except Exception as e:
        flash(f"Error verifying Launchpad team: {str(e)}", "negative")
        return redirect(url_for("dashboard.show_create_publisher"))

    try:
        new_publisher = Publisher(
            publisher_id=publisher_id,
            username=username,
            display_name=display_name,
        )
        db.session.add(new_publisher)
        db.session.commit()
        flash(f"Publisher '{display_name}' created successfully", "positive")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating publisher: {str(e)}", "negative")

    return redirect(url_for("dashboard.show_create_publisher"))
