from flask import jsonify
from flask import current_app as app

@app.route('/api/solutions', methods=['GET'])
def get_solutions():
    return jsonify("Solutions API"), 200

