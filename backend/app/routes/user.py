from flask import Blueprint, request
from app.utils.db import get_db
from app.utils.auth_middleware import token_required
from app.utils.response import success_response, error_response
from app.utils.logger import log_security_event
from werkzeug.security import generate_password_hash

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return success_response({
        'username': current_user['username'],
        'email': current_user['email'],
        'created_at': current_user['created_at']
    }, "Profile retrieved successfully", 200)

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    db = get_db()
    
    update_data = {}
    
    if 'email' in data and data['email'] != current_user['email']:
        if db.users.find_one({'email': data['email']}):
            return error_response("Email already in use", "EMAIL_IN_USE", 409)
        update_data['email'] = data['email']
        
    if 'password' in data and len(data['password']) >= 8:
        # Note: Ideally this should use the same validator as auth, but keeping simple for now
        update_data['password_hash'] = generate_password_hash(data['password'])
        
    if not update_data:
        return error_response("No valid updates provided", "BAD_REQUEST", 400)
        
    db.users.update_one(
        {'_id': current_user['_id']},
        {'$set': update_data}
    )
    
    log_security_event(db, str(current_user['_id']), "profile_update", None, request.remote_addr)
    
    return success_response(None, "Profile updated successfully", 200)

@user_bp.route('/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    db = get_db()
    alerts = list(db.alerts.find({'user_id': str(current_user['_id'])}).sort('timestamp', -1))
    
    for alert in alerts:
        alert['_id'] = str(alert['_id'])
        
    return success_response({'alerts': alerts}, "Alerts retrieved successfully", 200)

@user_bp.route('/alerts/<alert_id>/read', methods=['PUT'])
@token_required
def mark_alert_read(current_user, alert_id):
    from bson.objectid import ObjectId
    db = get_db()
    
    try:
        result = db.alerts.update_one(
            {'_id': ObjectId(alert_id), 'user_id': str(current_user['_id'])},
            {'$set': {'is_read': True}}
        )
        
        if result.modified_count == 1:
            return success_response(None, "Alert marked as read", 200)
        else:
            return error_response("Alert not found or already read", "NOT_FOUND", 404)
            
    except Exception as e:
        return error_response("Invalid alert ID", "BAD_REQUEST", 400)
