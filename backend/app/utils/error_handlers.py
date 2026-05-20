from marshmallow import ValidationError
from app.utils.response import error_response
import logging

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return error_response(
            message="Invalid input data",
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=e.messages
        )

    @app.errorhandler(400)
    def handle_400(e):
        return error_response("Bad Request", "BAD_REQUEST", 400)

    @app.errorhandler(401)
    def handle_401(e):
        return error_response("Unauthorized access", "UNAUTHORIZED", 401)

    @app.errorhandler(403)
    def handle_403(e):
        return error_response("Forbidden", "FORBIDDEN", 403)
        
    @app.errorhandler(404)
    def handle_404(e):
        return error_response("Resource not found", "NOT_FOUND", 404)
        
    @app.errorhandler(429)
    def handle_429(e):
        return error_response("Rate limit exceeded", "RATE_LIMIT_EXCEEDED", 429)

    @app.errorhandler(500)
    def handle_500(e):
        logging.error(f"Internal server error: {str(e)}")
        return error_response("Internal server error", "INTERNAL_ERROR", 500)

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logging.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return error_response("An unexpected error occurred", "INTERNAL_ERROR", 500)
