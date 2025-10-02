from app.extensions import db
from app.models import (
    PlatformTypes,
    Publisher,
    Solution,
    SolutionStatus,
    Creator,
    Visibility,
    Charm,
    UsefulLink,
    UseCase,
    Maintainer,
)
from app.utils import serialize_solution
from app.public.store_api import (
    get_publisher_details,
    get_user_details_by_email,
)
from app.exceptions import ValidationError
import uuid
import re
from sqlalchemy import inspect
from datetime import datetime, timezone


EDITABLE_FIELDS = {
    "title",
    "summary",
    "description",
    "icon",
    "terraform_modules",
    "documentation_main",
    "documentation_source",
    "get_started_url",
    "submit_bug_url",
    "community_discussion_url",
    "architecture_diagram_url",
    "architecture_explanation",
    "platform_version",
    "platform_prerequisites",
    "juju_versions",
}


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


def find_or_create_maintainer(email: str):
    maintainer = db.session.query(Maintainer).filter_by(email=email).first()

    if not maintainer:
        # Get user details from Store API (similar to how collaborators work)
        user_details = get_user_details_by_email(email)
        display_name = user_details.get("display_name") or email.split("@")[0]

        maintainer = Maintainer(email=email, display_name=display_name)
        db.session.add(maintainer)
        db.session.flush()
    else:
        if (
            not maintainer.display_name
            or maintainer.display_name == maintainer.email.split("@")[0]
        ):
            user_details = get_user_details_by_email(email)
            if user_details.get("display_name"):
                maintainer.display_name = user_details["display_name"]

    return maintainer


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

    if not re.match(r"^[\w\s']+$", title):
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
                    "(letters, numbers, underscores), spaces, "
                    "and apostrophes.",
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
        .filter(
            Publisher.username.in_(teams),
            Solution.status != SolutionStatus.UNPUBLISHED,
        )
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
            try:
                publisher_details = get_publisher_details(publisher)
                publisher_id = publisher_details["id"]
                display_name = publisher_details["display_name"]
                username = publisher_details["username"]
            except ValidationError:
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


def copy_charms_to_solution(
    source_solution, target_solution_id, new_charms_data=None
):
    if new_charms_data is not None:
        for charm_name in new_charms_data:
            if charm_name and charm_name.strip():
                charm = Charm(
                    charm_name=charm_name.strip(),
                    solution_id=target_solution_id,
                )
                db.session.add(charm)
    else:
        for old_charm in source_solution.charms:
            charm = Charm(
                charm_name=old_charm.charm_name, solution_id=target_solution_id
            )
            db.session.add(charm)


def copy_useful_links_to_solution(
    source_solution, target_solution_id, new_links_data=None
):
    if new_links_data is not None:
        for link_data in new_links_data:
            if link_data.get("title") and link_data.get("url"):
                useful_link = UsefulLink(
                    title=link_data["title"].strip(),
                    url=link_data["url"].strip(),
                    solution_id=target_solution_id,
                )
                db.session.add(useful_link)
    else:
        for old_link in source_solution.useful_links:
            useful_link = UsefulLink(
                title=old_link.title,
                url=old_link.url,
                solution_id=target_solution_id,
            )
            db.session.add(useful_link)


def copy_use_cases_to_solution(
    source_solution, target_solution_id, new_cases_data=None
):
    if new_cases_data is not None:
        for case_data in new_cases_data:
            if case_data.get("title") and case_data.get("description"):
                use_case = UseCase(
                    title=case_data["title"].strip(),
                    description=case_data["description"].strip(),
                    solution_id=target_solution_id,
                )
                db.session.add(use_case)
    else:
        for old_case in source_solution.use_cases:
            use_case = UseCase(
                title=old_case.title,
                description=old_case.description,
                solution_id=target_solution_id,
            )
            db.session.add(use_case)


def copy_maintainers_to_solution(
    source_solution, target_solution, new_maintainers_data=None
):
    if new_maintainers_data is not None:
        for email in new_maintainers_data:
            if email and email.strip():
                maintainer = find_or_create_maintainer(email.strip())
                if maintainer not in target_solution.maintainers:
                    target_solution.maintainers.append(maintainer)
    else:
        for old_maintainer in source_solution.maintainers:
            target_solution.maintainers.append(old_maintainer)


def update_solution_creator(
    solution, creator_email=None, mattermost_handle=None, matrix_handle=None
):
    if not any([creator_email, mattermost_handle, matrix_handle]):
        return

    current_creator = solution.creator

    if creator_email and creator_email.strip():
        if creator_email.strip() != current_creator.email:
            solution.creator = find_or_create_creator(
                creator_email.strip(), mattermost_handle, matrix_handle
            )
        else:
            if mattermost_handle is not None:
                current_creator.mattermost_handle = (
                    mattermost_handle.strip() or None
                )
            if matrix_handle is not None:
                current_creator.matrix_handle = matrix_handle.strip() or None
    else:
        if mattermost_handle is not None:
            current_creator.mattermost_handle = (
                mattermost_handle.strip() or None
            )
        if matrix_handle is not None:
            current_creator.matrix_handle = matrix_handle.strip() or None


def create_solution_revision(original_solution, metadata):
    mapper = inspect(Solution)
    data = {}
    for column in mapper.columns:
        if column.key not in ["id"]:
            data[column.key] = getattr(original_solution, column.key)

    for field, value in metadata.items():
        if field in EDITABLE_FIELDS:
            data[field] = value

    data["hash"] = uuid.uuid4().hex[:16]
    data["revision"] = original_solution.revision + 1
    data["status"] = SolutionStatus.PUBLISHED
    data["last_updated"] = datetime.now(timezone.utc)

    original_solution.status = SolutionStatus.UNPUBLISHED

    new_solution = Solution(**data)
    db.session.add(new_solution)
    db.session.flush()

    return new_solution


def update_published_solution(solution, metadata):
    new_solution = create_solution_revision(solution, metadata)

    copy_charms_to_solution(solution, new_solution.id, metadata.get("charms"))
    copy_useful_links_to_solution(
        solution, new_solution.id, metadata.get("useful_links")
    )
    copy_use_cases_to_solution(
        solution, new_solution.id, metadata.get("use_cases")
    )
    copy_maintainers_to_solution(
        solution, new_solution, metadata.get("maintainers")
    )

    update_solution_creator(
        new_solution,
        metadata.get("creator_email"),
        metadata.get("mattermost_handle"),
        metadata.get("matrix_handle"),
    )

    db.session.flush()
    db.session.commit()
    return serialize_solution(new_solution)


def update_draft_solution(solution, metadata):
    charms_data = metadata.pop("charms", None)
    useful_links_data = metadata.pop("useful_links", None)
    use_cases_data = metadata.pop("use_cases", None)
    maintainers_data = metadata.pop("maintainers", None)
    creator_email = metadata.pop("creator_email", None)
    mattermost_handle = metadata.pop("mattermost_handle", None)
    matrix_handle = metadata.pop("matrix_handle", None)

    for field, value in metadata.items():
        if field in EDITABLE_FIELDS:
            setattr(solution, field, value)

    if charms_data is not None:
        db.session.query(Charm).filter(
            Charm.solution_id == solution.id
        ).delete()
        copy_charms_to_solution(None, solution.id, charms_data)

    if useful_links_data is not None:
        db.session.query(UsefulLink).filter(
            UsefulLink.solution_id == solution.id
        ).delete()
        copy_useful_links_to_solution(None, solution.id, useful_links_data)

    if use_cases_data is not None:
        db.session.query(UseCase).filter(
            UseCase.solution_id == solution.id
        ).delete()
        copy_use_cases_to_solution(None, solution.id, use_cases_data)

    if maintainers_data is not None:
        solution.maintainers.clear()
        copy_maintainers_to_solution(None, solution, maintainers_data)

    update_solution_creator(
        solution, creator_email, mattermost_handle, matrix_handle
    )

    if solution.revision == 1:
        solution.status = SolutionStatus.PENDING_METADATA_REVIEW
    else:
        solution.status = SolutionStatus.PUBLISHED

    solution.last_updated = datetime.now(timezone.utc)

    db.session.commit()
    return serialize_solution(solution)


def update_solution_metadata(name: str, rev: int, metadata: dict):
    """
    Update solution metadata for a specific revision.
    For revision 1: sets status to PENDING_METADATA_REVIEW
    For revision >1: sets status to PUBLISHED (update without review)
    and increases revision number by 1
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

    if solution.status not in [SolutionStatus.DRAFT, SolutionStatus.PUBLISHED]:
        raise ValidationError(
            [
                {
                    "code": "invalid-status",
                    "message": "Solution cannot be edited in its current status",
                }
            ]
        )

    try:
        if solution.status == SolutionStatus.PUBLISHED:
            return update_published_solution(solution, metadata)
        else:
            return update_draft_solution(solution, metadata)

    except Exception:
        db.session.rollback()
        raise
