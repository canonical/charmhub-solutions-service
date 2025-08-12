from app.extensions import db
from app.models import Solution, SolutionStatus
from app.utils import serialize_solution


def approve_solution_name(name: str):
    solution = db.session.query(Solution).filter(Solution.name == name).first()
    if solution and solution.status == SolutionStatus.PENDING_NAME_REVIEW:
        solution.status = SolutionStatus.DRAFT
        db.session.commit()
        return serialize_solution(solution)
    return None


def approve_solution_metadata(name: str):
    solution = db.session.query(Solution).filter(Solution.name == name).first()
    if solution and solution.status == SolutionStatus.PENDING_METADATA_REVIEW:
        # Unpublish previous revision
        (
            db.session.query(Solution)
            .filter(
                Solution.name == name,
                Solution.status == SolutionStatus.PUBLISHED,
            )
            .update({"status": SolutionStatus.UNPUBLISHED})
        )
        solution.status = SolutionStatus.PUBLISHED
        db.session.commit()
        return serialize_solution(solution)
    return None


