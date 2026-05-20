from flask import Blueprint, request
from app.utils.response import success_response, error_response
from app.utils.validators import RegistrationSchema, LoginSchema
from app.utils.limiter import limiter
from app.utils.logger import log_security_event
from app.utils.db import get_db
from app.services.auth_service import register_user, authenticate_user
from marshmallow import ValidationError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    try:
        data = RegistrationSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response("Validation error", "VALIDATION_ERROR", 400, err.messages)
        
    user_id, error = register_user(data['username'], data['email'], data['password'])
    
    if error:
        return error_response(error, "REGISTRATION_FAILED", 409)
        
    return success_response({"user_id": user_id}, "User created successfully", 201)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        data = LoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return error_response("Validation error", "VALIDATION_ERROR", 400, err.messages)
        
    token, user, error = authenticate_user(data['username'], data['password'])
    
    db = get_db()
    if error:
        # Log failed login attempt
        log_security_event(db, None, "login_failed", f"Failed login for username: {data['username']}", request.remote_addr)
        return error_response(error, "AUTH_FAILED", 401)
        
    # Log successful login
    log_security_event(db, str(user['_id']), "login_success", None, request.remote_addr)
    
    return success_response({
        'token': token,
        'user': {
            'id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'role': user.get('role', 'user')
        }
    }, "Login successful")
