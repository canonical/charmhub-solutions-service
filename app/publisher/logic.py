from app.extensions import db
from app.models import (
    PlatformTypes,
    Publisher,
    Solution,
    SolutionStatus,
    Creator,
)
from app.utils import serialize_solution
import uuid
from sqlalchemy import inspect
from datetime import datetime, timezone


def get_solution_by_name(name: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
        )
        .first()
    )
    return serialize_solution(solution) if solution else None


def get_solutions_by_lp_teams(teams: list[str]):
    if not teams:
        return []

    solutions = (
        db.session.query(Solution)
        .join(Publisher, Solution.publisher_id == Publisher.publisher_id)
        .filter(Publisher.username.in_(teams))
        .all()
    )

    return [serialize_solution(solution) for solution in solutions]


def create_empty_solution(
    name: str,
    publisher: str,
    description: str,
    creator_email: str,
    mattermost_handle: str = None,
    matrix_handle: str = None,
):
    creator = (
        db.session.query(Creator)
        .filter(Creator.email == creator_email)
        .first()
    )
    if not creator:
        creator = Creator(
            email=creator_email,
            mattermost_handle=mattermost_handle,
            matrix_handle=matrix_handle,
        )
        db.session.add(creator)
        db.session.flush()
    else:
        if mattermost_handle:
            creator.mattermost_handle = mattermost_handle
        if matrix_handle:
            creator.matrix_handle = matrix_handle

    solution = Solution(
        hash=uuid.uuid4().hex[:16],
        revision=1,
        name=name,
        description=description,
        creator_id=creator.id,
        title=name,
        status=SolutionStatus.PENDING_NAME_REVIEW,
        publisher_id=publisher,
        platform=PlatformTypes.KUBERNETES,
    )
    db.session.add(solution)
    db.session.commit()
    return serialize_solution(solution)


def create_new_solution_revision(
    name: str,
    creator_email: str,
    mattermost_handle: str = None,
    matrix_handle: str = None,
):
    current_solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
            Solution.status == SolutionStatus.PUBLISHED,
        )
        .first()
    )

    if not current_solution:
        return None

    # Find or create creator for this revision
    creator = (
        db.session.query(Creator)
        .filter(Creator.email == creator_email)
        .first()
    )
    if not creator:
        creator = Creator(
            email=creator_email,
            mattermost_handle=mattermost_handle,
            matrix_handle=matrix_handle,
        )
        db.session.add(creator)
        db.session.flush()
    else:
        if mattermost_handle:
            creator.mattermost_handle = mattermost_handle
        if matrix_handle:
            creator.matrix_handle = matrix_handle

    mapper = inspect(Solution)
    data = {}
    for column in mapper.columns:
        if column.key not in ["id"]:
            data[column.key] = getattr(current_solution, column.key)

    data["hash"] = uuid.uuid4().hex[:16]
    data["revision"] = current_solution.revision + 1
    data["status"] = SolutionStatus.DRAFT
    data["creator_id"] = creator.id  # Set the new creator for this revision

    new_solution = Solution(**data)
    db.session.add(new_solution)
    db.session.commit()
    return serialize_solution(new_solution)


def get_draft_solution_by_name(name: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
            Solution.status == SolutionStatus.DRAFT,
        )
        .first()
    )
    return serialize_solution(solution) if solution else None


def get_solution_by_name_and_rev(name: str, rev: int):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
            Solution.revision == rev,
        )
        .first()
    )
    return serialize_solution(solution) if solution else None


def update_solution_metadata(name: str, rev: int, metadata: dict):
    """
    Update solution metadata for a specific revision.
    For revision 1: sets status to PENDING_METADATA_REVIEW
    For revision >1: sets status to PUBLISHED (update without review)
    """
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
            Solution.revision == rev,
        )
        .first()
    )

    if not solution:
        return None

    for field, value in metadata.items():
        if hasattr(solution, field) and field not in [
            "id",
            "hash",
            "name",
            "revision",
            "title",
            "created",
            "last_updated",
            "status",
        ]:
            setattr(solution, field, value)

    if rev == 1:
        solution.status = SolutionStatus.PENDING_METADATA_REVIEW
    else:
        solution.status = SolutionStatus.PUBLISHED

    solution.last_updated = datetime.now(timezone.utc)

    db.session.commit()
    return serialize_solution(solution)
