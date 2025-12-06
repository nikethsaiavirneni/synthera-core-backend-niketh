import logging
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.services.projects_service import ProjectService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProjectsRequestRouter:
    """Dispatch incoming API Gateway requests specifically for projects."""

    @classmethod
    def route_request(cls, http_method, resource_path, path_params, event):
        logger.info("🚀 Starting projects request routing")
        logger.info("HTTP Method: %s", http_method)
        logger.info("Resource Path: %s", resource_path)
        logger.info("Path Parameters: %s", path_params)
        logger.debug("Full Event: %s", event)
        
        entity_id = path_params.get("id")
        logger.info("Entity ID extracted: %s", entity_id)
        
        try:
            if http_method == "GET":
                logger.info("Processing GET request for projects")
                
                # Extract pagination and sorting parameters from query string.
                query_params = event.get("queryStringParameters") or {}
                logger.debug("Raw query parameters: %s", query_params)
                
                page = int(query_params.get("page", 1))
                limit = int(query_params.get("pageSize", query_params.get("limit", 10)))
                sort_by = query_params.get("sortBy", "project_name")
                sort_order = query_params.get("order", "asc")
                
                logger.info("Pagination parameters - Page: %d, Limit: %d", page, limit)
                logger.info("Sorting parameters - Sort By: %s, Order: %s", sort_by, sort_order)
                
                # Check for search functionality
                search_text = query_params.get("search")
                logger.info("Search text extracted: '%s'", search_text)
                
                # Check for lead_id filter for getting projects by lead
                lead_id = query_params.get("lead_id")
                logger.info("Lead ID filter extracted: %s", lead_id)
                
                # Parse advanced filters (any parameter with filter_ prefix gets special treatment)
                logger.info("🔍 Starting filter parsing process")
                filters = {}
                advanced_filters = {}
                
                logger.debug("Iterating through query parameters for filter detection")
                for key, value in query_params.items():
                    logger.debug("Processing parameter: %s = %s", key, value)
                    
                    if key.startswith("filter_"):
                        logger.debug("Advanced filter detected: %s", key)
                        # Advanced filter format: filter_column_name__operator=value
                        filter_parts = key[7:].split("__")  # Remove "filter_" prefix
                        logger.debug("Filter parts after splitting: %s", filter_parts)
                        
                        if len(filter_parts) == 2:
                            column_name, operator = filter_parts
                            advanced_filters[column_name] = {"operator": operator, "value": value}
                            logger.debug("Advanced filter added - Column: %s, Operator: %s, Value: %s", 
                                       column_name, operator, value)
                        else:
                            # Simple filter without operator (defaults to equals)
                            column_name = filter_parts[0]
                            advanced_filters[column_name] = {"operator": "equals", "value": value}
                            logger.debug("Simple filter added (defaults to equals) - Column: %s, Value: %s", 
                                       column_name, value)
                    elif key not in ["page", "limit", "pageSize", "sortBy", "order", "lead_id", "search"]:
                        # Standard filters (backwards compatibility)
                        filters[key] = value
                        logger.debug("Standard filter added: %s = %s", key, value)
                    else:
                        logger.debug("Parameter skipped (reserved): %s = %s", key, value)
                
                logger.info("Filter parsing completed - Standard filters: %d, Advanced filters: %d", 
                          len(filters), len(advanced_filters))
                logger.debug("Standard filters: %s", filters)
                logger.debug("Advanced filters: %s", advanced_filters)
                
                # Merge standard filters into advanced filters format
                logger.debug("Merging standard filters into advanced format")
                for key, value in filters.items():
                    if key not in advanced_filters:
                        advanced_filters[key] = {"operator": "equals", "value": value}
                        logger.debug("Merged standard filter: %s = %s (operator: equals)", key, value)
                
                logger.info("Final merged filters count: %d", len(advanced_filters))
                logger.debug("Final merged filters: %s", advanced_filters)
                
                # Determine which service method to call based on parameters
                logger.info("🎯 Determining route based on parameters")
                
                if entity_id:
                    logger.info("Route decision: GET single project by ID")
                    logger.debug("Calling ProjectService.get_project_by_id with entity_id: %s", entity_id)
                    response = ProjectService.get_project_by_id(entity_id)
                    logger.info("✅ Single project retrieval completed")
                    
                elif lead_id:
                    logger.info("Route decision: GET projects by lead ID")
                    logger.debug("Calling ProjectService.get_projects_by_lead_id with lead_id: %s", lead_id)
                    response = ProjectService.get_projects_by_lead_id(lead_id)
                    logger.info("✅ Projects by lead ID retrieval completed")
                    
                elif search_text or advanced_filters:
                    logger.info("Route decision: Advanced search")
                    logger.debug("Search parameters - Text: '%s', Filters: %s", search_text, advanced_filters)
                    logger.debug("Pagination - Page: %d, Limit: %d", page, limit)
                    logger.debug("Sorting - By: %s, Order: %s", sort_by, sort_order)
                    
                    # Use advanced search when search text or advanced filters are provided
                    response = ProjectService.advanced_search_projects(
                        search_text=search_text,
                        filters=advanced_filters if advanced_filters else None,
                        page=page,
                        limit=limit,
                        sort_by=sort_by,
                        sort_order=sort_order
                    )
                    logger.info("✅ Advanced search completed")
                    
                else:
                    logger.info("Route decision: GET all projects (standard)")
                    logger.debug("Standard parameters - Page: %d, Limit: %d, Sort: %s %s", 
                               page, limit, sort_by, sort_order)
                    logger.debug("Standard filters: %s", filters)
                    
                    response = ProjectService.get_all_projects(page=page, limit=limit,
                                                          sort_by=sort_by, sort_order=sort_order,
                                                          filters=filters)
                    logger.info("✅ Standard project listing completed")
                    
            elif http_method == "POST":
                logger.info("Processing POST request for project creation")
                logger.debug("Request body present: %s", "body" in event)
                logger.debug("Event keys: %s", list(event.keys()) if event else "None")
                response = ProjectService.create_project(event)
                logger.info("✅ Project creation request completed")
                
            elif http_method == "PUT" and entity_id:
                logger.info("Processing PUT request for project update")
                logger.info("Updating project with ID: %s", entity_id)
                logger.debug("Request body present: %s", "body" in event)
                response = ProjectService.update_project(int(entity_id), event)
                logger.info("✅ Project update request completed")
                
            elif http_method == "DELETE" and entity_id:
                logger.info("Processing DELETE request for project deletion")
                logger.info("Deleting project with ID: %s", entity_id)
                response = ProjectService.delete_project(int(entity_id))
                logger.info("✅ Project deletion request completed")
                
            elif http_method == "OPTIONS":
                logger.info("Processing OPTIONS request for CORS preflight")
                logger.debug("CORS preflight check - returning 200 with enhanced CORS headers")
                logger.debug("Request headers: %s", event.get("headers", {}))
                # Return enhanced CORS response for preflight requests
                cors_response = ResponseBuilder.build_cors_response(200, {"message": "CORS preflight successful"})
                logger.info("✅ CORS preflight response prepared")
                logger.debug("CORS response headers: %s", cors_response.get("headers", {}))
                return cors_response
                
            else:
                logger.warning("❌ Invalid request - Method: %s, Entity ID: %s", http_method, entity_id)
                logger.debug("Valid combinations: GET (with/without ID), POST, PUT (with ID), DELETE (with ID), OPTIONS")
                return ResponseBuilder.build_response(400, {"error": "Invalid request"})
            
            # Response processing and validation
            logger.info("📤 Processing service response")
            logger.debug("Response type: %s", type(response).__name__)
            
            # If the response is already in full response format, return it.
            if isinstance(response, dict) and "statusCode" in response and "body" in response:
                logger.info("Response already formatted - Status Code: %s", response.get("statusCode"))
                logger.debug("Response body type: %s", type(response.get("body")).__name__)
                return response
            # Otherwise, wrap it in a 200 response.
            else:
                logger.info("Wrapping response in 200 status")
                logger.debug("Original response type: %s", type(response).__name__)
                wrapped_response = ResponseBuilder.build_response(200, {"message": "Success", "data": response})
                logger.info("✅ Response successfully wrapped and ready to return")
                return wrapped_response
                
        except ValueError as ve:
            logger.error("❌ ValueError encountered in projects router")
            logger.error("Error details: %s", str(ve))
            logger.debug("ValueError traceback:", exc_info=True)
            logger.warning("Returning 400 Bad Request due to invalid input")
            return ResponseBuilder.build_response(400, {"error": str(ve)})
            
        except Exception as exc:
            logger.error("❌ Unexpected exception in projects router")
            logger.error("Exception type: %s", type(exc).__name__)
            logger.error("Exception message: %s", str(exc))
            logger.exception("Full exception traceback:", exc_info=True)
            logger.error("Request context - Method: %s, Path: %s, Params: %s", 
                        http_method, resource_path, path_params)
            logger.warning("Returning 500 Internal Server Error")
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})
