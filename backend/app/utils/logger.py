import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(app):
    """Set up the application logger with rotating file handler."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'phishguard.log')
    
    # 10MB max size, keep 5 backups
    file_handler = RotatingFileHandler(log_file, maxBytes=10240000, backupCount=5)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('PhishGuard startup')

def log_security_event(db, user_id, action, details=None, ip_address=None):
    """Log critical security events to MongoDB."""
    import datetime
    
    event = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.datetime.utcnow()
    }
    
    if details:
        event['details'] = details
    if ip_address:
        event['ip_address'] = ip_address
        
    db.activity_logs.insert_one(event)
