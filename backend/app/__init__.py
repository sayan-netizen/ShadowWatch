import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_talisman import Talisman

from app.config.settings import get_config
from app.utils.limiter import limiter
from app.utils.error_handlers import register_error_handlers
from app.utils.logger import setup_logger
from app.utils.db import init_db_indexes

def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config())
    
    # Setup CORS — restrict to the deployed frontend origin in production
    is_production = os.environ.get('FLASK_ENV', 'development') == 'production'
    frontend_url = os.environ.get('FRONTEND_URL', '*')
    cors_origins = [frontend_url] if is_production and frontend_url != '*' else "*"
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Setup Security Headers (CSP, HSTS, etc.)
    # force_https is enabled in production (Render terminates TLS at the edge).
    csp = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        'style-src': ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
        'font-src': ["'self'", "fonts.gstatic.com", "data:"],
        'img-src': ["'self'", "data:", "blob:"]
    }
    Talisman(app, content_security_policy=csp, force_https=is_production)
    
    # Setup Rate Limiting
    limiter.init_app(app)
    
    # Setup Logging
    setup_logger(app)
    
    # Setup Error Handlers
    register_error_handlers(app)
    
    # Initialize Database Indexes
    # Note: In a production environment with multiple workers, this might be better 
    # run as a separate migration script to avoid race conditions, but for this 
    # architecture, running on startup is acceptable.
    with app.app_context():
        init_db_indexes()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.scan import scan_bp
    # Assuming dashboard and user routes still exist and use the old patterns or are updated similarly.
    # We will register them. If they break due to auth middleware changes, we'll need to check them.
    from app.routes.dashboard import dashboard_bp
    from app.routes.user import user_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scan_bp, url_prefix='/api/scans')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(user_bp, url_prefix='/api/user')

    # Antigravity — Endpoint Monitoring Module
    from app.routes.endpoint import endpoint_bp
    app.register_blueprint(endpoint_bp, url_prefix='/api/endpoint')

    @app.route('/api/health')
    def health_check():
        return {"status": "ok", "message": "PhishGuard API is running securely"}

    return app
