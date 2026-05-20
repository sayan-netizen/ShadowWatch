from flask import Blueprint
from app.utils.db import get_db
from app.utils.auth_middleware import token_required
from app.utils.response import success_response

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    db = get_db()
    user_id = str(current_user['_id'])
    
    # Get total scans
    total_scans = db.scans.count_documents({'user_id': user_id})
    
    # Get scan breakdown by risk level
    high_risk = db.scans.count_documents({'user_id': user_id, 'risk_level': 'High'})
    medium_risk = db.scans.count_documents({'user_id': user_id, 'risk_level': 'Medium'})
    low_risk = db.scans.count_documents({'user_id': user_id, 'risk_level': 'Low'})
    safe_scans = db.scans.count_documents({'user_id': user_id, 'risk_level': 'Safe'})
    
    # Get recent activity
    recent_activity = list(db.activity_logs.find({'user_id': user_id}).sort('timestamp', -1).limit(5))
    for act in recent_activity:
        act['_id'] = str(act['_id'])
        
    # Get recent alerts count
    unread_alerts = db.alerts.count_documents({'user_id': user_id, 'is_read': False})
    
    stats = {
        'total_scans': total_scans,
        'risk_breakdown': {
            'high': high_risk,
            'medium': medium_risk,
            'low': low_risk,
            'safe': safe_scans
        },
        'recent_activity': recent_activity,
        'unread_alerts_count': unread_alerts
    }
    
    return success_response(stats, "Dashboard stats retrieved successfully", 200)
