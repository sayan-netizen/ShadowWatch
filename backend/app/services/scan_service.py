from app.utils.db import get_db
from app.services.keylogger_detector import perform_system_scan
import datetime

def process_system_scan(user_id):
    """Process a system scan, save results, and generate alerts if necessary."""
    scan_data = perform_system_scan()
    
    scan_result = {
        'user_id': str(user_id),
        'url': scan_data['target'], # keep url field for DB compatibility, but it's "Local System" now
        'risk_score': scan_data['risk_score'],
        'risk_level': scan_data['risk_level'],
        'indicators': scan_data['indicators'],
        'timestamp': datetime.datetime.utcnow()
    }
    
    db = get_db()
    result = db.scans.insert_one(scan_result)
    scan_result['_id'] = str(result.inserted_id)
    
    # Create alert if risk is high
    if scan_data['risk_level'] == "High":
        db.alerts.insert_one({
            'user_id': str(user_id),
            'message': "High risk activity detected during system scan!",
            'type': 'keylogger_alert',
            'is_read': False,
            'timestamp': datetime.datetime.utcnow()
        })
        
    return scan_result

def get_user_scan_history(user_id, limit=50):
    """Retrieve scan history for a user."""
    db = get_db()
    scans = list(db.scans.find({'user_id': str(user_id)}).sort('timestamp', -1).limit(limit))
    for scan in scans:
        scan['_id'] = str(scan['_id'])
    return scans
