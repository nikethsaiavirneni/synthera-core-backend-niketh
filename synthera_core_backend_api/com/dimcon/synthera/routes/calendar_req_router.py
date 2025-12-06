import logging
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CalendarRequestRouter:
    """Dispatch incoming API Gateway requests specifically for calendar."""

    @classmethod
    def route_request(cls, http_method, resource_path, path_params, event):
        logger.info("Routing calendar request: %s, params=%s", http_method, path_params)
        try:
            # Only support GET /calendar for month view
            path_parts = [part for part in resource_path.split('/') if part]
            if http_method == "GET" and (not path_parts or path_parts[0] == "calendar"):
                calendar_service = CalendarService()
                response = calendar_service.get_month_calendar(event)
                if isinstance(response, dict) and "statusCode" in response and "body" in response:
                    return response
                return ResponseBuilder.build_response(200, {"message": "Success", "data": response})
            elif http_method == "OPTIONS":
                logger.info("Processing OPTIONS request for CORS preflight")
                return ResponseBuilder.build_cors_response(200, {"message": "CORS preflight successful"})
            else:
                return ResponseBuilder.build_response(400, {"error": "Invalid request"})
        except ValueError as ve:
            logger.warning("Invalid input: %s", ve)
            return ResponseBuilder.build_response(400, {"error": str(ve)})
        except Exception as exc:
            logger.exception("Error processing calendar request", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})
