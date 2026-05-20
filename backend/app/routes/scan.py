from flask import Blueprint, request
from app.utils.auth_middleware import token_required
from app.utils.response import success_response, error_response
from app.utils.validators import AnalyzeURLSchema
from app.utils.limiter import limiter
from app.utils.logger import log_security_event
from app.utils.db import get_db
from app.services.scan_service import process_system_scan, get_user_scan_history
from marshmallow import ValidationError

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/analyze', methods=['POST'])
@token_required
@limiter.limit("20 per minute")
def analyze_system(current_user):
    # Process scan (no URL needed)
    scan_result = process_system_scan(current_user['_id'])
    
    # Log activity
    db = get_db()
    log_security_event(db, str(current_user['_id']), "system_scan", f"Performed local system scan", request.remote_addr)
    
    return success_response(scan_result, "Analysis complete", 200)

@scan_bp.route('/history', methods=['GET'])
@token_required
@limiter.limit("30 per minute")
def get_scan_history_route(current_user):
    scans = get_user_scan_history(current_user['_id'])
    return success_response({'history': scans}, "History retrieved successfully", 200)
