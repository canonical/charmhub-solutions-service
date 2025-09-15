from app.models import Solution


def serialize_solution(solution: Solution) -> dict:
    return {
        "id": solution.id,
        "name": solution.name,
        "hash": solution.hash,
        "revision": solution.revision,
        "status": solution.status.value,
        "visibility": solution.visibility.value,
        "title": solution.title,
        "summary": solution.summary,
        "description": solution.description,
        "terraform_modules": solution.terraform_modules,
        "created": solution.created.isoformat(),
        "last_updated": solution.last_updated.isoformat(),
        "publisher": {
            "id": solution.publisher.publisher_id,
            "display_name": solution.publisher.display_name,
            "username": solution.publisher.username,
        },
        "use_cases": [uc.to_dict() for uc in solution.use_cases],
        "deployable-on": [
            {
                "platform": (
                    solution.platform.value if solution.platform else None
                ),
                "version": solution.platform_version or [],
                "prerequisites": solution.platform_prerequisites or [],
            }
        ],
        "compatibility": {
            "juju_versions": solution.juju_versions or [],
        },
        "documentation": {
            "main": solution.documentation_main,
            "source": solution.documentation_source,
            "get_started": solution.get_started_url,
            "how_to_operate": solution.how_to_operate_url,
            "architecture_explanation": solution.architecture_explanation,
            "submit_a_bug": solution.submit_bug_url,
            "community_discussion": solution.community_discussion_url,
        },
        "media": {
            "icon": solution.icon,
            "architecture_diagram": solution.architecture_diagram_url,
        },
        "charms": [c.to_dict() for c in solution.charms],
        "maintainers": [m.to_dict() for m in solution.maintainers],
        "useful_links": [ul.to_dict() for ul in solution.useful_links],
        "creator": (
            {
                "email": solution.creator.email,
                "mattermost_handle": solution.creator.mattermost_handle,
                "matrix_handle": solution.creator.matrix_handle,
            }
            if solution.creator
            else None
        ),
    }
