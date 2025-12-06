import json
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.resources.leads.leads_details import LeadDetail
from com.dimcon.synthera.resources.leads.lead_stages import LeadStage
from com.dimcon.synthera.resources.organization_and_employees.employees import Employee
from com.dimcon.synthera.resources.base_dao import BaseDAO
from com.dimcon.synthera.utilities.log_handler import LoggerManager
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.utilities.search_utility import SearchUtility, ModelSearchConfig

import logging

logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

class LeadService:
    """
    Service layer for managing lead operations. Uses DAO for database access
    and DBSessionUtil for consistent session handling.
    """
    engine = get_engine()
    dao = BaseDAO(engine)
    db_util = DBSessionUtil(engine)

    @classmethod
    def get_all_leads(cls, page=1, limit=10, sort_by="lead_first_name", sort_order="asc", filters=None):
        """Retrieve a paginated list of leads."""
        try:
            logger.debug("Service: get_all_leads called.")
            with cls.db_util.session_scope() as session:
                # fetch_all now returns a dict with "results" and "total_count"
                result = cls.dao.fetch_all(session, LeadDetail, page=page, limit=limit,
                                            sort_by=sort_by, sort_order=sort_order, filters=filters)
                lead_list = [lead.to_dict() for lead in result.get("results", [])]
                total_count = result.get("total_count", 0)
            logger.debug(f"Service: Retrieved {len(lead_list)} leads.")
            return ResponseBuilder.build_response(200, {"message": "Success", "data": lead_list, "total_count": total_count})
        except Exception as e:
            logger.error("Service: Error fetching all leads", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def get_lead_by_id(cls, lead_id):
        """Retrieve a single lead by its ID."""
        try:
            logger.debug(f"Service: get_lead_by_id called with id {lead_id}.")
            
            # Validate lead_id is an integer
            try:
                lead_id = int(lead_id)
            except (ValueError, TypeError):
                logger.error("Service: Provided lead_id is not a valid integer.")
                return ResponseBuilder.build_response(400, {"error": "Invalid lead ID"})

            with cls.db_util.session_scope() as session:
                lead = cls.dao.fetch_by_id(session, LeadDetail, lead_id)
                if not lead:
                    return ResponseBuilder.build_response(404, {"error": "Lead not found"})
                lead_dict = lead.to_dict()
            logger.debug("Service: Lead found successfully.")
            return ResponseBuilder.build_response(200, {"message": "Success", "data": lead_dict})
        except Exception as e:
            logger.error("Service: Error fetching lead by id", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def advanced_search_leads(cls, search_text=None, filters=None, page=1, limit=10, sort_by="lead_first_name", sort_order="asc"):
        """
        Perform advanced search on leads using the SearchUtility.
        
        Args:
            search_text: Global text search across lead_first_name, lead_last_name, lead_email, lead_company_name
            filters: Dictionary of advanced filters with operators
                    Example: {
                        "lead_status": {"operator": "equals", "value": "active"},
                        "lead_first_name": {"operator": "contains", "value": "john"},
                        "created_at": {"operator": "date_range", "start": "2025-01-01", "end": "2025-12-31"}
                    }
            page: Page number for pagination
            limit: Number of records per page
            sort_by: Column to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            ResponseBuilder response with search results
        """
        try:
            logger.debug(f"Service: advanced_search_leads called with search_text='{search_text}', filters={filters}")
            
            with cls.db_util.session_scope() as session:
                # Use SearchUtility for advanced search
                search_result = SearchUtility.advanced_search(
                    session=session,
                    model=LeadDetail,
                    search_text=search_text,
                    search_columns=ModelSearchConfig.get_default_search_columns("LeadDetail"),
                    filters=filters,
                    page=page,
                    limit=limit,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                
                # Convert results to dictionaries
                lead_list = [lead.to_dict() for lead in search_result["results"]]
                
                # Build response with pagination metadata
                response_data = {
                    "message": "Search completed successfully",
                    "data": lead_list,
                    "total_count": search_result["total_count"],
                    "page": search_result["page"],
                    "limit": search_result["limit"],
                    "total_pages": search_result["total_pages"],
                    "has_next": search_result["has_next"],
                    "has_prev": search_result["has_prev"],
                    "search_metadata": {
                        "search_text": search_result["search_text"],
                        "filters_applied": search_result["filters_applied"],
                        "searchable_columns": ModelSearchConfig.get_searchable_columns("LeadDetail")
                    }
                }
                
            logger.debug(f"Service: Advanced search completed - {len(lead_list)} results found")
            return ResponseBuilder.build_response(200, response_data)
            
        except Exception as e:
            logger.error("Service: Error in advanced_search_leads", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def create_lead(cls, event: dict):
        """Create a new lead."""
        try:
            if "body" not in event:
                logger.debug("Missing request body")
                return ResponseBuilder.build_response(400, {"error": "Missing request body"})

            try:
                lead_data = json.loads(event["body"])
            except json.JSONDecodeError:
                logger.debug("Invalid JSON format")
                return ResponseBuilder.build_response(400, {"error": "Invalid JSON format"})

            if not isinstance(lead_data, dict):
                logger.debug("Request body must be a JSON object")
                return ResponseBuilder.build_response(400, {"error": "Request body must be a JSON object"})

            logger.debug(f"Event received: {event}")
            logger.debug(f"Parsed lead data: {lead_data}")

            required_fields = ["lead_first_name", "lead_last_name"]
            if not all(field in lead_data for field in required_fields):
                logger.debug(f"Missing required fields: {required_fields}")
                return ResponseBuilder.build_response(400, {"error": "Missing required fields"})

            new_lead = LeadDetail(**lead_data)

            # Use the db_util instance to manage the session
            with cls.db_util.session_scope() as session:
                session.add(new_lead)
                session.commit()

                return ResponseBuilder.build_response(200, {
                    "message": "Success",
                    "data": new_lead.to_dict()
                })

        except TypeError as e:
            logger.debug(f"TypeError: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": str(e)})
        except Exception as e:
            logger.error(f"Service: Error creating lead: {str(e)}", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def update_lead(cls, lead_id, event):
        """Update an existing lead using provided lead ID and event data."""
        try:
            logger.debug(f"Service: update_lead called for id {lead_id}.")
            
            if "body" not in event:
                return ResponseBuilder.build_response(400, {"error": "Invalid request"})
                
            try:
                update_data = json.loads(event["body"])
            except json.JSONDecodeError:
                return ResponseBuilder.build_response(400, {"error": "Invalid request"})

            with cls.db_util.session_scope() as session:
                updated = cls.dao.update(session, LeadDetail, lead_id, update_data)
                session.commit()
                session.refresh(updated)
                lead_dict = updated.to_dict()
            logger.debug("Service: Lead updated successfully.")
            return ResponseBuilder.build_response(200, {"message": "Success", "data": lead_dict})
        except Exception as e:
            logger.error("Service: Error updating lead", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def delete_lead(cls, lead_id):
        """Delete a lead by its ID."""
        try:
            logger.debug(f"Service: delete_lead called for id {lead_id}.")
            with cls.db_util.session_scope() as session:
                cls.dao.delete(session, LeadDetail, lead_id)
                session.commit()
            logger.debug("Service: Lead deleted successfully.")
            return ResponseBuilder.build_response(200, {"message": "Lead deleted successfully"})
        except Exception as e:
            logger.error("Service: Error deleting lead", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def get_all_lead_stages(cls):
        """Return all lead stages."""
        try:
            with cls.db_util.session_scope() as session:
                stages = session.query(LeadStage).all()
                stage_list = [
                    {
                        "lead_stage_id": s.lead_stage_id,
                        "stage_name": s.stage_name,
                        "description": s.description,
                        "created_by": s.created_by,
                        "updated_by": s.updated_by,
                        "created_at": s.created_at,
                        "updated_at": s.updated_at
                    }
                    for s in stages
                ]
            return ResponseBuilder.build_response(200, {"message": "Success", "data": stage_list})
        except Exception as e:
            logger.error("Error fetching lead stages", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def create_lead_stage(cls, event: dict):
        """Create a new lead stage using cognito_sub from token."""
        try:
            if "body" not in event:
                return ResponseBuilder.build_response(400, {"error": "Missing request body"})
            try:
                stage_data = json.loads(event["body"])
            except Exception:
                return ResponseBuilder.build_response(400, {"error": "Invalid JSON format"})
            required_fields = ["stage_name", "description"]
            if not all(field in stage_data for field in required_fields):
                return ResponseBuilder.build_response(400, {"error": "Missing required fields"})
            
            # Extract cognito_sub from authorizer claims
            cognito_sub = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
            if not cognito_sub:
                return ResponseBuilder.build_response(401, {"error": "Unauthorized: Missing Cognito sub"})
            
            with cls.db_util.session_scope() as session:
                employee = session.query(Employee).filter_by(cognito_sub=cognito_sub).first()
                if not employee:
                    return ResponseBuilder.build_response(401, {"error": "Employee not found"})
                emp_id = employee.emp_id

                # Create and add new stage
                new_stage = LeadStage(
                    stage_name=stage_data["stage_name"],
                    description=stage_data["description"],
                    created_by=emp_id,
                    updated_by=emp_id
                )
                session.add(new_stage)
                session.commit()
                # Extract attributes before session closes
                stage_dict = {
                    "lead_stage_id": new_stage.lead_stage_id,
                    "stage_name": new_stage.stage_name,
                    "description": new_stage.description,
                    "created_by": new_stage.created_by,
                    "updated_by": new_stage.updated_by,
                    "created_at": str(new_stage.created_at),
                    "updated_at": str(new_stage.updated_at)
                }
            return ResponseBuilder.build_response(200, {
                "message": "Success",
                "data": stage_dict
            })
        except Exception as e:
            logger.error("Error creating lead stage", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})
