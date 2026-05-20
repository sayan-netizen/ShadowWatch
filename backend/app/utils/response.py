from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    """Standardized success response format."""
    response = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code

def error_response(message="An error occurred", error_code="INTERNAL_ERROR", status_code=500, details=None):
    """Standardized error response format."""
    response = {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
    if details is not None:
        response["details"] = details
    return jsonify(response), status_code
