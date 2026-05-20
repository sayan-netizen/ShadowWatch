from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from app.utils.db import get_db
from flask import current_app

def register_user(username, email, password):
    """Register a new user."""
    db = get_db()
    
    # Check if user exists
    if db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
        return None, "User with this username or email already exists"
        
    hashed_password = generate_password_hash(password)
    
    # First user gets admin role, others get user role
    role = 'user'
    if db.users.count_documents({}) == 0:
        role = 'admin'
        
    new_user = {
        'username': username,
        'email': email,
        'password_hash': hashed_password,
        'role': role,
        'created_at': datetime.datetime.utcnow()
    }
    
    result = db.users.insert_one(new_user)
    return str(result.inserted_id), None

def authenticate_user(username, password):
    """Authenticate a user and return a JWT token."""
    db = get_db()
    user = db.users.find_one({'username': username})
    
    if not user or not check_password_hash(user['password_hash'], password):
        return None, None, "Invalid username or password"
        
    token = jwt.encode({
        'user_id': str(user['_id']),
        'role': user.get('role', 'user'),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    return token, user, None
