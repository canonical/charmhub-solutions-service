from app.extensions import db
from app.models import Solution, SolutionStatus, Visibility
from app.utils import serialize_solution


def _published_public_filter():
    return (
        Solution.status == SolutionStatus.PUBLISHED,
        Solution.visibility == Visibility.PUBLIC,
    )


def get_all_published_solutions():
    solutions = (
        db.session.query(Solution).filter(*_published_public_filter()).all()
    )
    return [serialize_solution(solution) for solution in solutions]


def get_published_solution_by_name(name: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.name == name,
            *_published_public_filter(),
        )
        .order_by(Solution.revision.desc())
        .first()
    )
    return serialize_solution(solution) if solution else None


def search_published_solutions(query: str):
    if not query:
        return []

    results = (
        db.session.query(Solution)
        .filter(
            *_published_public_filter(),
            (
                Solution.title.ilike(f"%{query}%")
                | Solution.summary.ilike(f"%{query}%")
                | Solution.description.ilike(f"%{query}%")
            ),
        )
        .all()
    )
    return [serialize_solution(solution) for solution in results]


def get_published_solution_by_hash(hash: str):
    solution = (
        db.session.query(Solution)
        .filter(
            Solution.hash == hash,
        )
        .first()
    )

    if not solution:
        return None

    # if solution is published and public, return it
    if (
        solution.status == SolutionStatus.PUBLISHED
        and solution.visibility == Visibility.PUBLIC
    ):
        return serialize_solution(solution)

    # allow previewing pending solutions (for review dashboard)
    if solution.status in [
        SolutionStatus.PENDING_NAME_REVIEW,
        SolutionStatus.PENDING_METADATA_REVIEW,
    ]:
        return serialize_solution(solution)

    # if solution is unpublished, try to find the latest published revision
    if solution.status == SolutionStatus.UNPUBLISHED:
        latest_published = (
            db.session.query(Solution)
            .filter(
                Solution.name == solution.name,
                *_published_public_filter(),
            )
            .order_by(Solution.revision.desc())
            .first()
        )
        if latest_published:
            return serialize_solution(latest_published)

    # solution exists but is not published/public and no published version found
    return None
