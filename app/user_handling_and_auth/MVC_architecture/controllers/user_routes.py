from flask import request, jsonify, session, Blueprint
from app.user_handling_and_auth.MVC_architecture.controllers.user_controllers import UserController

from ..user_validators.user_validators import (
    validate_user_registration,
    validate_user_login,
    validate_user_update,
)


user_blueprint = Blueprint('user', __name__, url_prefix='/api/v1/users')


@user_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    valid, msg = validate_user_registration(data)
    if not valid:
        return jsonify({"error": msg}), 400
    user_controller = UserController()
    result, status = user_controller.register_user(data)
    return jsonify(result), status

@user_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    valid, msg = validate_user_login(data)
    if not valid:
        return jsonify({"error": msg}), 400
    user_controller = UserController()
    result, status = user_controller.login_user(data['username'], data['password'])
    if status == 200:
        session['user_id'] = result['id']
    return jsonify(result), status


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User is not logged in"}), 401

    user_controller = UserController()
    result, status = user_controller.logout_user(user_id)
    if status == 200:
        session.pop('user_id', None)
    return jsonify(result), status

@user_blueprint.route('/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user_controller = UserController()
    result, status = user_controller.get_user_by_id(user_id)
    return jsonify(result), status

@user_blueprint.route('/all_users', methods=['GET'])
#@required_role(UserRole.ADMIN)
def get_all_users():
    user_controller = UserController()
    result, status = user_controller.get_all_users()
    return jsonify(result), status

@user_blueprint.route('/<int:user_id>', methods=['PUT'])
#@required_role(UserRole.ADMIN)
def update_user(user_id):
    data = request.get_json()
    valid, msg = validate_user_update(data)
    if not valid:
        return jsonify({"error": msg}), 400
    user_controller = UserController()
    result, status = user_controller.update_user(user_id, data)
    return jsonify(result), status

@user_blueprint.route('/<int:user_id>', methods=['DELETE'])
#@required_role(UserRole.ADMIN)
def delete_user(user_id):
    user_controller = UserController()
    result, status = user_controller.delete_user(user_id)
    return jsonify(result), status


