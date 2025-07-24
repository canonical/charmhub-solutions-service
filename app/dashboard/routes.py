from flask import Blueprint, render_template
from app.models import Solution
from sqlalchemy.orm import joinedload

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    solutions_query = Solution.query.options(
        joinedload(Solution.publisher)
    ).all()
    solutions_context = [
        {
            "name": solution.name,
            "title": solution.title,
            "status": solution.status.value,
            "publisher_username": solution.publisher.username,
            "publisher_display_name": solution.publisher.display_name,
        }
        for solution in solutions_query
    ]
    return render_template("dashboard.html", solutions=solutions_context)
