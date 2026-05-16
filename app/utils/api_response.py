from flask import jsonify


def success(data=None, message="Success"):
    body = {"success": True, "message": message, "data": data}
    return jsonify(body), 200


def created(data=None, message="Created"):
    body = {"success": True, "message": message, "data": data}
    return jsonify(body), 201


def no_result(message="No result"):
    body = {"success": True, "message": message, "data": None}
    return jsonify(body), 200


def bad_request(message="Bad request", errors=None):
    body = {"success": False, "message": message}
    if errors is not None:
        body["errors"] = errors
    return jsonify(body), 400


def not_found(message="Not found"):
    return jsonify({"success": False, "message": message}), 404
