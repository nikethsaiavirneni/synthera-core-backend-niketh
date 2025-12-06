# com/dimcon/synthera/routes/zoom_req_router.py
import logging
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.services.zoom_auth_service import ZoomAuthService
from com.dimcon.synthera.services.zoom_meeting_service import ZoomMeetingService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ZoomRequestRouter:
    @classmethod
    def route_request(cls, http_method, resource_path, path_params, event):
        try:
            rp = (resource_path or "").rstrip("/")

            # 1) SETUP (saves Zoom client creds & returns authorization URL)
            if rp.endswith("/zoom/setup") and http_method == "POST":
                return ZoomAuthService.route_setup(event)

            # 2) CREATE MEETING
            if rp.endswith("/zoom/create") and http_method == "POST":
                return ZoomMeetingService.route_create(event)

            # 3) UPDATE MEETING
            if rp.endswith("/zoom/update") and http_method == "PATCH":
                return ZoomMeetingService.route_update(event)

            # 4) DELETE MEETING
            if rp.endswith("/zoom/delete") and http_method == "DELETE":
                return ZoomMeetingService.route_delete(event)

            # 5) GET MEETINGS
            if rp.endswith("/zoom/meetings") and http_method == "GET":
                return ZoomMeetingService.route_fetch(event)

            # 6) ZOOM OAUTH CALLBACK
            if rp.endswith("/zoom/callback") and http_method == "GET":
                # Extract code and state from query params
                qs = event.get("queryStringParameters") or {}
                code = qs.get("code")
                state = qs.get("state")
                
                logger.info("Processing Zoom OAuth callback - code: %s, state: %s", 
                           "present" if code else "missing", state or "missing")
                
                if not code or not state:
                    logger.warning("Missing required parameters in OAuth callback - code: %s, state: %s", 
                                  bool(code), bool(state))
                    # Redirect to frontend with error
                    return {
                        "statusCode": 302,
                        "headers": {
                            "Location": "https://syntheraai.com/activities/meetings?zoom_error=missing_params"
                        }
                    }
                
                # Call the OAuth handler (state is usually app_user_id/email)
                try:
                    logger.info("Calling OAuth handler for user: %s", state)
                    result = ZoomAuthService.handle_oauth_callback(code, state)
                    logger.info("OAuth callback completed successfully for user: %s", state)
                    # Redirect to frontend with success
                    return {
                        "statusCode": 302,
                        "headers": {
                            "Location": "https://syntheraai.com/activities/meetings?zoom_connected=true"
                        }
                    }
                except Exception as e:
                    logger.error("OAuth callback failed for user %s: %s", state, str(e))
                    # Redirect to frontend with error
                    return {
                        "statusCode": 302,
                        "headers": {
                            "Location": f"https://syntheraai.com/activities/meetings?zoom_error={str(e)[:100]}"
                        }
                    }

            # nothing else is exposed
            return ResponseBuilder.build_response(404, {"error": "Unknown Zoom route"})
        except Exception as e:
            return ResponseBuilder.build_response(500, {"error": "Internal server error", "details": str(e)})
