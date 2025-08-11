from app.extensions import db
from app.models import PlatformTypes, Publisher, Solution, SolutionStatus
from app.utils import serialize_solution
import uuid
from sqlalchemy import inspect


def get_all_published_solutions():
    solutions = (
        db.session.query(Solution)
        .filter(Solution.status == SolutionStatus.PUBLISHED)
        .all()
    )
    return [serialize_solution(solution) for solution in solutions]


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


def get_solution_by_name(name: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
        )
        .first()
    )
    return serialize_solution(solution) if solution else None


def get_published_solution_by_name(name: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
            Solution.status == SolutionStatus.PUBLISHED,
        )
        .first()
    )
    return serialize_solution(solution) if solution else None


def search_published_solutions(query: str):
    if not query:
        return []

    results = (
        db.session.query(Solution)
        .filter(
            Solution.status == SolutionStatus.PUBLISHED,
            (
                Solution.title.ilike(f"%{query}%")
                | Solution.summary.ilike(f"%{query}%")
                | Solution.description.ilike(f"%{query}%")
            ),
        )
        .all()
    )
    return [serialize_solution(solution) for solution in results]


def get_solution_by_hash(hash: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.hash == hash,
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
    name: str, publisher: str, description: str, created_by: str
):
    solution = Solution(
        hash=uuid.uuid4().hex[:16],
        revision=1,
        name=name,
        description=description,
        created_by=created_by,
        title=name,
        status=SolutionStatus.PENDING_NAME_REVIEW,
        publisher_id=publisher,
        platform=PlatformTypes.KUBERNETES,
    )
    db.session.add(solution)
    db.session.commit()
    return serialize_solution(solution)


def create_new_solution_revision(name: str):
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

    mapper = inspect(Solution)
    data = {}
    for column in mapper.columns:
        if column.key not in ["id"]:
            data[column.key] = getattr(current_solution, column.key)

    data["hash"] = uuid.uuid4().hex[:16]
    data["revision"] = current_solution.revision + 1
    data["status"] = SolutionStatus.DRAFT

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
