from app.extensions import db
from app.models import (
    PlatformTypes,
    Publisher,
    Solution,
    SolutionStatus,
    Creator,
    Visibility,
    Creator,
)
from app.utils import serialize_solution
from app.public.store_api import get_publisher_details
from app.exceptions import ValidationError
import uuid
import re
from sqlalchemy import inspect
from datetime import datetime, timezone


def find_or_create_creator(
    creator_email: str,
    mattermost_handle: str = None,
    matrix_handle: str = None,
):
    creator = (
        db.session.query(Creator).filter(Creator.email == creator_email).first()
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

    return creator


def validate_solution_name(name: str) -> bool:
    if not name:
        return False

    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name):
        return False

    if not re.search(r"[a-z]", name):
        return False

    return True


def validate_solution_title(title: str) -> bool:
    if not title:
        return False

    if not re.match(r"^[\w\s]+$", title):
        return False

    return True


def register_solution_package(
    teams: list,
    name: str,
    publisher: str,
    summary: str,
    creator: Creator,
    title: str = None,
    platform: str = "kubernetes",
):
    if not validate_solution_name(name):
        raise ValidationError(
            [
                {
                    "code": "invalid-name",
                    "message": "Name format is invalid. "
                    "Must be lowercase letters, numbers, "
                    "and hyphens only, with at least one letter. "
                    "The name cannot start or end with a hyphen.",
                }
            ]
        )

    if title and not validate_solution_title(title):
        raise ValidationError(
            [
                {
                    "code": "invalid-title",
                    "message": "Title format is invalid. "
                    "Must contain only word characters "
                    "(letters, numbers, underscores) and spaces.",
                }
            ]
        )

    existing_solution = get_solution_by_name(name)
    if existing_solution:
        raise ValidationError(
            [
                {
                    "code": "already-registered",
                    "message": "A solution with this name " "already exists.",
                }
            ]
        )

    if publisher not in teams:
        raise ValidationError(
            [
                {
                    "code": "access-denied",
                    "message": "User must be a member of publishing group",
                }
            ]
        )

    return create_empty_solution(
        name=name,
        publisher=publisher,
        summary=summary,
        creator=creator,
        title=title,
        platform=platform,
    )


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
    summary: str,
    creator: Creator,
    title: str = None,
    platform: str = "kubernetes",
):
    try:

        publisher_record = (
            db.session.query(Publisher)
            .filter(Publisher.username == publisher)
            .first()
        )

        if not publisher_record:
            publisher_details = get_publisher_details(publisher)

            if publisher_details and publisher_details.get("id"):
                publisher_id = publisher_details["id"]
                display_name = publisher_details["display_name"]
                username = publisher_details["username"]
            else:
                publisher_id = publisher
                display_name = publisher
                username = publisher

            publisher_record = Publisher(
                publisher_id=publisher_id,
                username=username,
                display_name=display_name,
            )
            db.session.add(publisher_record)
            db.session.flush()

        platform_type = PlatformTypes.KUBERNETES
        if platform.lower() == "machine":
            platform_type = PlatformTypes.MACHINE

        solution = Solution(
            hash=uuid.uuid4().hex[:16],
            revision=1,
            name=name,
            summary=summary,
            creator_id=creator.id,
            title=title or name,
            status=SolutionStatus.PENDING_NAME_REVIEW,
            publisher_id=publisher_record.publisher_id,
            platform=platform_type,
            visibility=Visibility.PRIVATE,
        )
        db.session.add(solution)
        db.session.commit()
        return serialize_solution(solution)

    except Exception:
        db.session.rollback()
        raise


def create_new_solution_revision(
    name: str,
    creator: Creator,
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

    try:

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

    except Exception:
        db.session.rollback()
        raise


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
