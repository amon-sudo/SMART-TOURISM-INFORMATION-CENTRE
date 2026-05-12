from flask import Blueprint, request, jsonify
from ..controllers.controllers import (
    get_all_settings, update_user_profile, update_accessibility_settings, 
    update_notification_settings, update_user_preferences
)
# from flask_jwt_extended import jwt_required, get_jwt_identity

user_settings_bp = Blueprint('user_settings', __name__)

@user_settings_bp.route('/settings', methods=['GET'])
# @jwt_required()
def fetch_user_settings(user_id=1):
    """Exposes all user settings. (Logic: user_id = get_jwt_identity() or 1)"""
    # user_id = get_jwt_identity()
    return get_all_settings(user_id)

@user_settings_bp.route('/settings/profile', methods=['PATCH'])
# @jwt_required()
def patch_profile(user_id=1):
    # user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        from app.utils.responses import ApiResponse
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_user_profile(user_id, data)

@user_settings_bp.route('/settings/accessibility', methods=['PATCH'])
# @jwt_required()
def patch_accessibility(user_id=1):
    # user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        from app.utils.responses import ApiResponse
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_accessibility_settings(user_id, data)

@user_settings_bp.route('/settings/notifications', methods=['PATCH'])
# @jwt_required()
def patch_notifications(user_id=1):
    # user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        from app.utils.responses import ApiResponse
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_notification_settings(user_id, data)

@user_settings_bp.route('/settings/preferences', methods=['PATCH'])
# @jwt_required()
def patch_preferences(user_id=1):
    # user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        from app.utils.responses import ApiResponse
        return ApiResponse.error(message="No data provided", status_code=400)
    return update_user_preferences(user_id, data)
