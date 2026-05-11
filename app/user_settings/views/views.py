from flask import Blueprint, request, jsonify
from ..controllers.controllers import (
    get_all_settings, update_user_profile, update_accessibility_settings, 
    update_notification_settings, update_user_preferences
)
from ..utils.auth_middleware import token_required

user_settings_bp = Blueprint('user_settings', __name__)

@user_settings_bp.route('/settings', methods=['GET'])
@token_required
def fetch_user_settings(user_id):
    """Exposes all user settings from profiles, accessibility, notifications, and preferences."""
    result, status_code = get_all_settings(user_id)
    return jsonify(result), status_code

@user_settings_bp.route('/settings/profile', methods=['PATCH'])
@token_required
def patch_profile(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    result, status_code = update_user_profile(user_id, data)
    return jsonify(result), status_code

@user_settings_bp.route('/settings/accessibility', methods=['PATCH'])
@token_required
def patch_accessibility(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    result, status_code = update_accessibility_settings(user_id, data)
    return jsonify(result), status_code

@user_settings_bp.route('/settings/notifications', methods=['PATCH'])
@token_required
def patch_notifications(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    result, status_code = update_notification_settings(user_id, data)
    return jsonify(result), status_code

@user_settings_bp.route('/settings/preferences', methods=['PATCH'])
@token_required
def patch_preferences(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    result, status_code = update_user_preferences(user_id, data)
    return jsonify(result), status_code
