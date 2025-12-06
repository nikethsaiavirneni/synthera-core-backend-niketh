import json
import logging
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.services.tasks_service import TasksService
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TasksRequestRouter:
    """
    Router for handling task-related API requests.
    Provides comprehensive CRUD operations for tasks with advanced search,
    filtering, pagination, and sorting capabilities.
    """

    @classmethod
    def route_request(cls, http_method: str, resource_path: str, path_params: dict, event: dict):
        """
        Route incoming task requests to appropriate handlers.
        
        Args:
            http_method: HTTP method (GET, POST, PUT, DELETE)
            resource_path: API resource path
            path_params: Path parameters including ID
            event: Complete API Gateway event
            
        Returns:
            HTTP response dictionary
        """
        logger.info(f"🎯 Routing tasks request: {http_method} {resource_path}, params={path_params}")
        
        try:
            # Initialize tasks service with authentication
            cognito_utility = CognitoUserUtility()
            tasks_service = TasksService(cognito_utility)
            
            # Route based on HTTP method
            if http_method == "GET":
                return cls._handle_get_request(tasks_service, resource_path, path_params, event)
            elif http_method == "POST":
                return cls._handle_post_request(tasks_service, resource_path, path_params, event)
            elif http_method == "PUT":
                return cls._handle_put_request(tasks_service, resource_path, path_params, event)
            elif http_method == "DELETE":
                return cls._handle_delete_request(tasks_service, resource_path, path_params, event)
            else:
                logger.warning(f"Unsupported HTTP method: {http_method}")
                return ResponseBuilder.build_response(405, {"error": "Method not allowed"})
                
        except ValueError as e:
            logger.error(f"❌ Validation error in tasks router: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": str(e)})
        except Exception as e:
            logger.error(f"❌ Unexpected error in tasks router: {str(e)}")
            logger.exception("Tasks router error details:")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def _handle_get_request(cls, service: TasksService, resource_path: str, path_params: dict, event: dict):
        """
        Handle GET requests for task data with advanced search and filtering.
        
        Args:
            service: Tasks service instance
            resource_path: API resource path
            path_params: Path parameters
            event: API Gateway event
            
        Returns:
            HTTP response dictionary
        """
        logger.debug("Handling GET request for tasks")
        entity_id = path_params.get("id")
        
        try:
            # Extract query parameters for pagination, sorting, and filtering
            query_params = event.get("queryStringParameters") or {}
            
            # Parse pagination parameters
            page = int(query_params.get("page", 1))
            limit = int(query_params.get("pageSize", query_params.get("limit", 50)))
            sort_by = query_params.get("sortBy", "created_date")
            sort_order = query_params.get("order", "desc")
            
            # Check for search functionality
            search_text = query_params.get("search")
            
            # Parse advanced filters (filter_column__operator=value format)
            advanced_filters = {}
            for key, value in query_params.items():
                if key.startswith("filter_"):
                    filter_parts = key[7:].split("__")  # Remove "filter_" prefix
                    if len(filter_parts) == 2:
                        column_name, operator = filter_parts
                        advanced_filters[column_name] = {"operator": operator, "value": value}
                    else:
                        column_name = filter_parts[0]
                        advanced_filters[column_name] = {"operator": "equals", "value": value}
            
            if entity_id:
                # GET /tasks/{id} - Get specific task
                logger.info(f"📋 Routing to get task by ID: {entity_id}")
                response = service.get_task_by_id(entity_id, event)
                
            else:
                # GET /tasks - List tasks with advanced search
                logger.info("📋 Routing to tasks list")
                
                # Parse the resource path for sub-endpoints
                path_parts = [part for part in resource_path.split('/') if part]
                if len(path_parts) >= 1 and path_parts[0] == 'tasks':
                    remaining_parts = path_parts[1:]
                else:
                    remaining_parts = path_parts
                
                if not remaining_parts:
                    # GET /tasks - Main tasks listing
                    response = service.list_tasks(
                        event=event,
                        page=page,
                        limit=limit,
                        sort_by=sort_by,
                        sort_order=sort_order,
                        search_text=search_text,
                        filters=advanced_filters
                    )
                    
                elif len(remaining_parts) == 1:
                    endpoint = remaining_parts[0]
                    
                    if endpoint == "assigned":
                        # GET /tasks/assigned - Get tasks assigned to current user
                        logger.info("👤 Routing to assigned tasks")
                        response = service.get_assigned_tasks(
                            event=event,
                            page=page,
                            limit=limit,
                            sort_by=sort_by,
                            sort_order=sort_order,
                            search_text=search_text,
                            filters=advanced_filters
                        )
                        
                    elif endpoint == "created":
                        # GET /tasks/created - Get tasks created by current user
                        logger.info("✏️ Routing to created tasks")
                        response = service.get_created_tasks(
                            event=event,
                            page=page,
                            limit=limit,
                            sort_by=sort_by,
                            sort_order=sort_order,
                            search_text=search_text,
                            filters=advanced_filters
                        )
                        
                    elif endpoint == "overdue":
                        # GET /tasks/overdue - Get overdue tasks
                        logger.info("⏰ Routing to overdue tasks")
                        response = service.get_overdue_tasks(
                            event=event,
                            page=page,
                            limit=limit,
                            sort_by=sort_by,
                            sort_order=sort_order,
                            search_text=search_text,
                            filters=advanced_filters
                        )
                        
                    elif endpoint == "completed":
                        # GET /tasks/completed - Get completed tasks
                        logger.info("✅ Routing to completed tasks")
                        response = service.get_completed_tasks(
                            event=event,
                            page=page,
                            limit=limit,
                            sort_by=sort_by,
                            sort_order=sort_order,
                            search_text=search_text,
                            filters=advanced_filters
                        )
                        
                    else:
                        logger.warning(f"Unknown tasks endpoint: {endpoint}")
                        return ResponseBuilder.build_response(404, {"error": "Tasks endpoint not found"})
                        
                else:
                    logger.warning(f"Unsupported tasks path: {'/'.join(remaining_parts)}")
                    return ResponseBuilder.build_response(404, {"error": "Tasks resource not found"})
            
            # If the response is already in full response format, return it
            if isinstance(response, dict) and "statusCode" in response and "body" in response:
                return response
            # Otherwise, wrap it in a 200 response
            return ResponseBuilder.build_response(200, {"message": "Success", "data": response})
                
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            logger.exception("GET request error details:")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def _handle_post_request(cls, service: TasksService, resource_path: str, path_params: dict, event: dict):
        """
        Handle POST requests for creating tasks.
        
        Args:
            service: Tasks service instance
            resource_path: API resource path
            path_params: Path parameters
            event: API Gateway event
            
        Returns:
            HTTP response dictionary
        """
        logger.debug("Handling POST request for tasks")
        
        try:
            # Parse request body
            request_body = json.loads(event.get("body", "{}"))
            logger.debug(f"Request body keys: {list(request_body.keys())}")
            
            # Parse the resource path
            path_parts = [part for part in resource_path.split('/') if part]
            if len(path_parts) >= 1 and path_parts[0] == 'tasks':
                remaining_parts = path_parts[1:]
            else:
                remaining_parts = path_parts
            
            # Validate required fields for task creation
            required_fields = ["title", "description"]
            missing_fields = [field for field in required_fields if field not in request_body]
            
            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                return ResponseBuilder.build_response(400, {
                    "error": "Missing required fields",
                    "missing_fields": missing_fields,
                    "required_fields": required_fields
                })
            
            if not remaining_parts:
                # POST /tasks - Create new task
                logger.info("📝 Routing to create task")
                response = service.create_task(event)
                
            elif len(remaining_parts) == 1:
                endpoint = remaining_parts[0]
                
                if endpoint == "assign":
                    # POST /tasks/assign - Assign existing task to user
                    logger.info("👤 Routing to task assignment")
                    required_assignment_fields = ["task_id", "assignee_id"]
                    missing_assignment_fields = [field for field in required_assignment_fields 
                                               if field not in request_body]
                    
                    if missing_assignment_fields:
                        return ResponseBuilder.build_response(400, {
                            "error": "Missing required fields for assignment",
                            "missing_fields": missing_assignment_fields,
                            "required_fields": required_assignment_fields
                        })
                    
                    response = service.assign_task(event)
                    
                else:
                    logger.warning(f"Unknown tasks POST endpoint: {endpoint}")
                    return ResponseBuilder.build_response(404, {"error": "Tasks endpoint not found"})
                    
            else:
                logger.warning(f"Unsupported tasks POST path: {'/'.join(remaining_parts)}")
                return ResponseBuilder.build_response(404, {"error": "Tasks resource not found"})
            
            # If the response is already in full response format, return it
            if isinstance(response, dict) and "statusCode" in response and "body" in response:
                return response
            # Otherwise, wrap it in a 201 response
            return ResponseBuilder.build_response(201, {"message": "Created successfully", "data": response})
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": "Invalid JSON in request body"})
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": str(e)})
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            logger.exception("POST request error details:")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def _handle_put_request(cls, service: TasksService, resource_path: str, path_params: dict, event: dict):
        """
        Handle PUT requests for updating tasks.
        
        Args:
            service: Tasks service instance
            resource_path: API resource path
            path_params: Path parameters
            event: API Gateway event
            
        Returns:
            HTTP response dictionary
        """
        logger.debug("Handling PUT request for tasks")
        
        try:
            # Extract entity ID from path parameters
            entity_id = path_params.get("id")
            logger.debug(f"Entity ID: {entity_id}")
            
            if not entity_id:
                logger.warning("Missing entity ID for PUT request")
                return ResponseBuilder.build_response(400, {"error": "Missing task ID"})
            
            # Parse request body
            request_body = json.loads(event.get("body", "{}"))
            logger.debug(f"Request body keys: {list(request_body.keys())}")
            
            # Parse the resource path
            path_parts = [part for part in resource_path.split('/') if part]
            if len(path_parts) >= 1 and path_parts[0] == 'tasks':
                remaining_parts = path_parts[1:]
            else:
                remaining_parts = path_parts
            
            if len(remaining_parts) >= 1:
                endpoint = remaining_parts[0]
                
                if endpoint == entity_id:
                    # PUT /tasks/{id} - Update task
                    logger.info(f"📝 Routing to task update for ID: {entity_id}")
                    response = service.update_task(entity_id, event)
                    
                elif len(remaining_parts) >= 2 and remaining_parts[1] == "status":
                    # PUT /tasks/{id}/status - Update task status
                    logger.info(f"🔄 Routing to task status update for ID: {entity_id}")
                    
                    if "status" not in request_body:
                        return ResponseBuilder.build_response(400, {
                            "error": "Missing required field: status"
                        })
                    
                    response = service.update_task_status(entity_id, event)
                    
                elif len(remaining_parts) >= 2 and remaining_parts[1] == "complete":
                    # PUT /tasks/{id}/complete - Mark task as complete
                    logger.info(f"✅ Routing to task completion for ID: {entity_id}")
                    response = service.complete_task(entity_id, event)
                    
                else:
                    logger.warning(f"Unknown tasks PUT endpoint: {'/'.join(remaining_parts)}")
                    return ResponseBuilder.build_response(404, {"error": "Tasks endpoint not found"})
                    
            else:
                logger.warning("Missing task ID in PUT request path")
                return ResponseBuilder.build_response(400, {"error": "Missing task ID in path"})
            
            # If the response is already in full response format, return it
            if isinstance(response, dict) and "statusCode" in response and "body" in response:
                return response
            # Otherwise, wrap it in a 200 response
            return ResponseBuilder.build_response(200, {"message": "Updated successfully", "data": response})
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": "Invalid JSON in request body"})
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": str(e)})
        except Exception as e:
            logger.error(f"Error handling PUT request: {str(e)}")
            logger.exception("PUT request error details:")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def _handle_delete_request(cls, service: TasksService, resource_path: str, path_params: dict, event: dict):
        """
        Handle DELETE requests for removing tasks.
        
        Args:
            service: Tasks service instance
            resource_path: API resource path
            path_params: Path parameters
            event: API Gateway event
            
        Returns:
            HTTP response dictionary
        """
        logger.debug("Handling DELETE request for tasks")
        
        try:
            # Extract entity ID from path parameters
            entity_id = path_params.get("id")
            logger.debug(f"Entity ID: {entity_id}")
            
            if not entity_id:
                logger.warning("Missing entity ID for DELETE request")
                return ResponseBuilder.build_response(400, {"error": "Missing task ID"})
            
            # Parse the resource path
            path_parts = [part for part in resource_path.split('/') if part]
            if len(path_parts) >= 1 and path_parts[0] == 'tasks':
                remaining_parts = path_parts[1:]
            else:
                remaining_parts = path_parts
            
            if len(remaining_parts) >= 1 and remaining_parts[0] == entity_id:
                # DELETE /tasks/{id} - Delete task
                logger.info(f"🗑️ Routing to task deletion for ID: {entity_id}")
                response = service.delete_task(entity_id, event)
                
                # If the response is already in full response format, return it
                if isinstance(response, dict) and "statusCode" in response and "body" in response:
                    return response
                # Otherwise, wrap it in a 200 response
                return ResponseBuilder.build_response(200, {"message": "Deleted successfully", "data": response})
                
            else:
                logger.warning(f"Invalid DELETE path for tasks: {'/'.join(remaining_parts)}")
                return ResponseBuilder.build_response(404, {"error": "Tasks resource not found"})
                
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": str(e)})
        except Exception as e:
            logger.error(f"Error handling DELETE request: {str(e)}")
            logger.exception("DELETE request error details:")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    logger.info("Testing TasksRequestRouter")
    
    # Mock event for testing
    test_event = {
        "httpMethod": "GET",
        "resource": "/tasks",
        "pathParameters": None,
        "queryStringParameters": {"page": "1", "limit": "10"},
        "body": None
    }
    
    try:
        response = TasksRequestRouter.route_request("GET", "/tasks", {}, test_event)
        logger.info(f"Test response: {response}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
