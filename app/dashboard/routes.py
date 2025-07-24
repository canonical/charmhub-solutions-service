from flask import Blueprint, render_template
from app.models import Solution, SolutionStatus
from sqlalchemy.orm import joinedload

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    solutions_query = Solution.query.options(
        joinedload(Solution.publisher)
    ).all()

    published_solutions = []
    pending_review_solutions = []
    unpublished_solutions = []
    pending_solutions = []

    for solution in solutions_query:
        solution_data = {
            "name": solution.name,
            "title": solution.title,
            "status": solution.status.value,
            "publisher_username": solution.publisher.username,
            "publisher_display_name": solution.publisher.display_name,
        }
        if solution.status == SolutionStatus.PUBLISHED:
            published_solutions.append(solution_data)
        elif solution.status == SolutionStatus.PENDING_REVIEW:
            pending_review_solutions.append(solution_data)
        elif solution.status == SolutionStatus.UNPUBLISHED:
            unpublished_solutions.append(solution_data)
        elif solution.status == SolutionStatus.PENDING:
            pending_solutions.append(solution_data)

    return render_template(
        "dashboard.html",
        published_solutions=published_solutions,
        pending_review_solutions=pending_review_solutions,
        unpublished_solutions=unpublished_solutions,
        pending_solutions=pending_solutions,
    )
