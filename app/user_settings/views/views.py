from flask import Blueprint, request, jsonify
from ..controllers.controllers import get_settings, update_settings
from ...utils.auth_middleware import token_required

user_settings_bp = Blueprint('user_settings', __name__)

@user_settings_bp.route('/settings', methods=['GET'])
@token_required
def fetch_user_settings(user_id):
    """
    Exposes the user settings from profiles, accessibility, and notifications tables.
    """
    settings = get_settings(user_id)
    return jsonify(settings), 200

@user_settings_bp.route('/settings', methods=['PATCH'])
@token_required
def patch_user_settings(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
        
    result, status_code = update_settings(user_id, data)
    return jsonify(result), status_code
