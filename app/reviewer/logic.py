from datetime import datetime, timezone
from app.extensions import db
from app.models import (
    Solution,
    SolutionStatus,
    ReviewAction,
    ReviewerActionType,
    Visibility,
)
from app.utils import serialize_solution


def approve_solution_name(name: str, reviewer_id: str):
    solution = db.session.query(Solution).filter(Solution.name == name).first()
    if solution and solution.status == SolutionStatus.PENDING_NAME_REVIEW:
        solution.status = SolutionStatus.DRAFT
        solution.approved_by = reviewer_id
        review_action = ReviewAction(
            solution_id=solution.id,
            reviewer_id=reviewer_id,
            action=ReviewerActionType.APPROVE_REGISTRATION,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(review_action)
        db.session.commit()
        return serialize_solution(solution)
    return None


def approve_solution_metadata(name: str, reviewer_id: str):
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
        solution.visibility = Visibility.PUBLIC
        solution.approved_by = reviewer_id

        review_action = ReviewAction(
            solution_id=solution.id,
            reviewer_id=reviewer_id,
            action=ReviewerActionType.PUBLISH,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(review_action)
        db.session.commit()
        return serialize_solution(solution)
    return None
