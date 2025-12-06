from com.dimcon.synthera.services.industry_services import IndustryService
from com.dimcon.synthera.utilities.responses import ResponseBuilder
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class IndustryRequestRouter:
    @classmethod
    def route_request(cls, http_method, resource_path, path_params, event):
        logger.info("Routing industry request: %s, params=%s", http_method, path_params)
        try:
            if resource_path.strip("/").lower() == "industries":
                if http_method == "GET":
                    return IndustryService.get_all_industries()
                elif http_method == "POST":
                    return IndustryService.create_industry(event)
                elif http_method == "OPTIONS":
                    return ResponseBuilder.build_cors_response(200, {"message": "CORS preflight successful"})
                else:
                    return ResponseBuilder.build_response(400, {"error": "Invalid request"})
            else:
                return ResponseBuilder.build_response(404, {"error": "Resource not found"})
        except Exception as exc:
            logger.exception("Error processing industry request", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})