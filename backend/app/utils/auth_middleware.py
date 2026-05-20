from functools import wraps
from flask import request, current_app
import jwt
from app.utils.db import get_db
from app.utils.response import error_response
from bson.objectid import ObjectId
import logging

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header
                
        if not token:
            return error_response("Token is missing!", "TOKEN_MISSING", 401)
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            db = get_db()
            current_user = db.users.find_one({'_id': ObjectId(data['user_id'])})
            if not current_user:
                return error_response("User not found!", "USER_NOT_FOUND", 401)
                
        except jwt.ExpiredSignatureError:
            return error_response("Token has expired!", "TOKEN_EXPIRED", 401)
        except Exception as e:
            logging.error(f"JWT Decode Error: {str(e)}")
            return error_response("Token is invalid!", "TOKEN_INVALID", 401)
            
        return f(current_user, *args, **kwargs)
        
    return decorated

def require_role(role):
    """Decorator to require a specific role for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            user_role = current_user.get('role', 'user')
            if user_role != role and user_role != 'admin':
                return error_response("Insufficient permissions", "FORBIDDEN", 403)
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator
