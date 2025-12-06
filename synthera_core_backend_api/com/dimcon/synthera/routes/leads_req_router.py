import logging
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.services.leads_services import LeadService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LeadsRequestRouter:
    """Dispatch incoming API Gateway requests specifically for leads."""

    @classmethod
    def route_request(cls, http_method, resource_path, path_params, event):
        logger.info("Routing leads request: %s, params=%s", http_method, path_params)
        entity_id = path_params.get("id")
        try:
            # --- Lead stages endpoints ---
            if resource_path.strip("/").lower() == "lead-stages":
                if http_method == "GET":
                    return LeadService.get_all_lead_stages()
                elif http_method == "POST":
                    return LeadService.create_lead_stage(event)
                elif http_method == "OPTIONS":
                    logger.info("Processing OPTIONS request for CORS preflight")
                    return ResponseBuilder.build_cors_response(200, {"message": "CORS preflight successful"})
                else:
                    return ResponseBuilder.build_response(400, {"error": "Invalid request"})
            
            # --- Existing lead endpoints ---
            if http_method == "GET":
                # Extract pagination and sorting parameters from query string.
                query_params = event.get("queryStringParameters") or {}
                page = int(query_params.get("page", 1))
                limit = int(query_params.get("pageSize", query_params.get("limit", 10)))
                sort_by = query_params.get("sortBy", "lead_first_name")
                sort_order = query_params.get("order", "asc")
                
                # Check for search functionality
                search_text = query_params.get("search")
                
                # Parse advanced filters (any parameter with filter_ prefix gets special treatment)
                filters = {}
                advanced_filters = {}
                
                for key, value in query_params.items():
                    if key.startswith("filter_"):
                        # Advanced filter format: filter_column_name__operator=value
                        filter_parts = key[7:].split("__")  # Remove "filter_" prefix
                        if len(filter_parts) == 2:
                            column_name, operator = filter_parts
                            advanced_filters[column_name] = {"operator": operator, "value": value}
                        else:
                            # Simple filter without operator (defaults to equals)
                            column_name = filter_parts[0]
                            advanced_filters[column_name] = {"operator": "equals", "value": value}
                    elif key not in ["page", "limit", "pageSize", "sortBy", "order", "search"]:
                        # Standard filters (backwards compatibility)
                        filters[key] = value
                
                # Merge standard filters into advanced filters format
                for key, value in filters.items():
                    if key not in advanced_filters:
                        advanced_filters[key] = {"operator": "equals", "value": value}
                
                if entity_id:
                    response = LeadService.get_lead_by_id(entity_id)
                elif search_text or advanced_filters:
                    # Use advanced search when search text or advanced filters are provided
                    response = LeadService.advanced_search_leads(
                        search_text=search_text,
                        filters=advanced_filters if advanced_filters else None,
                        page=page,
                        limit=limit,
                        sort_by=sort_by,
                        sort_order=sort_order
                    )
                else:
                    response = LeadService.get_all_leads(page=page, limit=limit,
                                                          sort_by=sort_by, sort_order=sort_order,
                                                          filters=filters)
            elif http_method == "POST":
                response = LeadService.create_lead(event)
            elif http_method == "PUT" and entity_id:
                response = LeadService.update_lead(int(entity_id), event)
            elif http_method == "DELETE" and entity_id:
                response = LeadService.delete_lead(int(entity_id))
            elif http_method == "OPTIONS":
                logger.info("Processing OPTIONS request for CORS preflight")
                return ResponseBuilder.build_cors_response(200, {"message": "CORS preflight successful"})
            else:
                return ResponseBuilder.build_response(400, {"error": "Invalid request"})
            
            # If the response is already in full response format, return it.
            if isinstance(response, dict) and "statusCode" in response and "body" in response:
                return response
            # Otherwise, wrap it in a 200 response.
            return ResponseBuilder.build_response(200, {"message": "Success", "data": response})
        except ValueError as ve:
            logger.warning("Invalid input: %s", ve)
            return ResponseBuilder.build_response(400, {"error": str(ve)})
        except Exception as exc:
            logger.exception("Error processing leads request", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})