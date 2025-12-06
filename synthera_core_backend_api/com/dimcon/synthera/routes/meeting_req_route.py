import logging
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.services.meetings_service import MeetingService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MeetingRequestRouter:
    """Dispatch incoming API Gateway requests specifically for meetings."""

    @classmethod
    def route_request(cls, http_method, path_params, event):
        logger.info("Routing meetings request: %s, params=%s", http_method, path_params)
        entity_id = path_params.get("id")
        try:
            if http_method == "GET":
                # Extract query parameters for pagination and sorting.
                query_params = event.get("queryStringParameters") or {}
                if entity_id:
                    response = MeetingService.get_by_id(entity_id)
                else:
                    page = int(query_params.get("page", 1))
                    limit = int(query_params.get("limit", 10))
                    sort_by = query_params.get("sortby", "meeting_id")  # now using lowercase
                    sort_order = query_params.get("order", "asc")
                    filters = {k: v for k, v in query_params.items() if k not in ["page", "limit", "sortby", "order"]}
                    response = MeetingService.get_all_meetings(event, page=page, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters)
            elif http_method == "POST":
                response = MeetingService.create(event)
            elif http_method == "PUT" and entity_id:
                response = MeetingService.update(entity_id, event)
            elif http_method == "DELETE" and entity_id:
                response = MeetingService.delete(entity_id)
            elif http_method == "OPTIONS":
                logger.info("Processing OPTIONS request for CORS preflight")
                return ResponseBuilder.build_cors_response(200, {"message": "CORS preflight successful"})
            else:
                return ResponseBuilder.build_response(400, {"error": "Invalid request"})
            
            # If the response is already in full format, return it.
            if isinstance(response, dict) and "statusCode" in response and "body" in response:
                return response
            # Wrap the response in a 200 response.
            return ResponseBuilder.build_response(200, {"message": "Success", "data": response})
        except ValueError as ve:
            logger.warning("Invalid input: %s", ve)
            return ResponseBuilder.build_response(400, {"error": str(ve)})
        except Exception as exc:
            logger.exception("Error processing meetings request", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})