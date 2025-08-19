from app.extensions import db
from app.models import Solution, SolutionStatus
from app.utils import serialize_solution


def get_all_published_solutions():
    solutions = (
        db.session.query(Solution)
        .filter(Solution.status == SolutionStatus.PUBLISHED)
        .all()
    )
    return [serialize_solution(solution) for solution in solutions]


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
