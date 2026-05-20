import os
from dotenv import load_dotenv

# Ensure environment variables are loaded before configuration classes are defined
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not SECRET_KEY or SECRET_KEY == 'default_secret':
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set securely.")
        
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = 'phishguard'
    
    # JWT Config
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 3600 # 24 hours
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'
    # In production, enforce stricter security headers via Talisman (configured in __init__)

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
