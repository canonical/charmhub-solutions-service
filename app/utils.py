from app.models import Solution

def serialize_solution(solution: Solution) -> dict:
    return {
        "name": solution.name,
        "title": solution.title,
        "summary": solution.summary,
        "description": solution.description,
        "terraform_modules": solution.terraform_modules,
        "icon": solution.icon,
        "last_updated": solution.last_updated.isoformat(),
        "platform": solution.platform.value if solution.platform else None,
        "platform_version": solution.platform_version,
        "platform_prerequisites": solution.platform_prerequisites,
        "documentation_main": solution.documentation_main,
        "documentation_source": solution.documentation_source,
        "get_started_url": solution.get_started_url,
        "how_to_operate_url": solution.how_to_operate_url,
        "architecture_diagram_url": solution.architecture_diagram_url,
        "architecture_explanation": solution.architecture_explanation,
        "submit_bug_url": solution.submit_bug_url,
        "community_discussion_url": solution.community_discussion_url,
        "juju_versions": solution.juju_versions,
        "publisher": {
            "id": solution.publisher.publisher_id,
            "display_name": solution.publisher.display_name,
            "username": solution.publisher.username,
        },
        "use_cases": [uc.to_dict() for uc in solution.use_cases],
        "charms": [c.to_dict() for c in solution.charms],
        "maintainers": [m.to_dict() for m in solution.maintainers],
        "useful_links": [ul.to_dict() for ul in solution.useful_links],
    }
