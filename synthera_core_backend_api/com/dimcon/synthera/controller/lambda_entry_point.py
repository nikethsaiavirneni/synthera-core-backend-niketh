import logging
import json
import os
from com.dimcon.synthera.routes.leads_req_router import LeadsRequestRouter
from com.dimcon.synthera.routes.projects_req_router import ProjectsRequestRouter
from com.dimcon.synthera.routes.meeting_req_route import MeetingRequestRouter
from com.dimcon.synthera.routes.calendar_req_router import CalendarRequestRouter
from com.dimcon.synthera.routes.tasks_router import TasksRequestRouter
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility
from com.dimcon.synthera.routes.industry_req_router import IndustryRequestRouter
from synthera_core_backend_api.com.dimcon.synthera.routes.zoom_req_router import ZoomRequestRouter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Lambda event: {json.dumps(event)}")

    # --- PATCH: Detect Cognito Post Confirmation trigger ---
    if event.get("triggerSource") == "PostConfirmation_ConfirmSignUp" and "request" in event:
        user_attrs = event['request']['userAttributes']
        cognito_sub = user_attrs.get('sub')
        email = user_attrs.get('email')
        username = user_attrs.get('cognito:username') or user_attrs.get('preferred_username', '')
        claims = user_attrs

        cognito_util = CognitoUserUtility()
        user_context = cognito_util.auto_register_cognito_user(
            cognito_sub=cognito_sub,
            email=email,
            username=username,
            claims=claims
        )

        logger.info(f"User registration result: {user_context}")
        return event  # Cognito expects the event to be returned

    # --- Existing API Gateway routing logic ---
    http_method = event.get("httpMethod")
    resource_path = event.get("resource")
    if resource_path is None:
        return ResponseBuilder.build_response(400, {"error": "Missing 'resource' in event."})
    if http_method is None:
        return ResponseBuilder.build_response(400, {"error": "Missing 'httpMethod' in event."})

    path_params = event.get("pathParameters") or {}
    # Determine the primary resource (e.g., 'leads' or 'meetings') 
    resource = resource_path.strip("/").split("/")[0].lower()

    if resource == "leads":
        return LeadsRequestRouter.route_request(http_method, resource_path, path_params, event)
    elif resource == "lead-stages":
        return LeadsRequestRouter.route_request(http_method, resource_path, path_params, event)
    elif resource == "projects":
        return ProjectsRequestRouter.route_request(http_method, resource_path, path_params, event)
    elif resource == "meetings":
        return MeetingRequestRouter.route_request(http_method, path_params, event)
    elif resource == "calendar":
        return CalendarRequestRouter.route_request(http_method, resource_path, path_params, event)
    elif resource == "tasks":
        return TasksRequestRouter.route_request(http_method, resource_path, path_params, event)
    elif resource == "industries":
        return IndustryRequestRouter.route_request(http_method, resource_path, path_params, event)
    elif resource == "zoom": 
        return ZoomRequestRouter.route_request(http_method, resource_path, path_params, event)
    else:
        return ResponseBuilder.build_response(404, {"error": "Resource not found"})
