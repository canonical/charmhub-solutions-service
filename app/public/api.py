from flask import Blueprint, request, jsonify
from app.public.logic import (
    get_all_published_solutions,
    get_published_solution_by_name,
    search_published_solutions,
)
from app.utils import login_redirect_response

public_bp = Blueprint("public", __name__)


@public_bp.route("/login", methods=["GET"])
def login_redirect():
    return login_redirect_response()


@public_bp.route("/solutions", methods=["GET"])
def list_published_solutions():
    solutions = get_all_published_solutions()
    return jsonify(solutions), 200


@public_bp.route("/solutions/<string:name>", methods=["GET"])
def get_solution(name):
    solution = get_published_solution_by_name(name)
    if not solution:
        return jsonify({"error": "Solution not found"}), 404
    return jsonify(solution), 200


@public_bp.route("/solutions/search", methods=["GET"])
def search_solutions():
    query = request.args.get("q", "")
    results = search_published_solutions(query)
    return jsonify(results), 200
