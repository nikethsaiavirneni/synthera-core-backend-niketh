import json
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.resources.projects.projects_lead import Project
from com.dimcon.synthera.resources.base_dao import BaseDAO
from com.dimcon.synthera.utilities.log_handler import LoggerManager
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.utilities.search_utility import SearchUtility, ModelSearchConfig

import logging

logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

class ProjectService:
    """
    Service layer for managing project operations. Uses DAO for database access
    and DBSessionUtil for consistent session handling.
    """
    engine = get_engine()
    dao = BaseDAO(engine)
    db_util = DBSessionUtil(engine)

    @classmethod
    def get_all_projects(cls, page=1, limit=10, sort_by="project_name", sort_order="asc", filters=None):
        """Retrieve a paginated list of projects."""
        try:
            logger.debug("Service: get_all_projects called.")
            with cls.db_util.session_scope() as session:
                # fetch_all now returns a dict with "results" and "total_count"
                result = cls.dao.fetch_all(session, Project, page=page, limit=limit,
                                            sort_by=sort_by, sort_order=sort_order, filters=filters)
                project_list = [project.to_dict() for project in result.get("results", [])]
                total_count = result.get("total_count", 0)
            logger.debug(f"Service: Retrieved {len(project_list)} projects.")
            return ResponseBuilder.build_response(200, {"message": "Success", "data": project_list, "total_count": total_count})
        except Exception as e:
            logger.error("Service: Error fetching all projects", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def get_project_by_id(cls, project_id):
        """Retrieve a single project by its ID."""
        try:
            logger.debug(f"Service: get_project_by_id called with id {project_id}.")
            
            # Validate project_id is an integer
            try:
                project_id = int(project_id)
            except (ValueError, TypeError):
                logger.error("Service: Provided project_id is not a valid integer.")
                return ResponseBuilder.build_response(400, {"error": "Invalid project ID"})

            with cls.db_util.session_scope() as session:
                project = cls.dao.fetch_by_id(session, Project, project_id)
                if not project:
                    return ResponseBuilder.build_response(404, {"error": "Project not found"})
                project_dict = project.to_dict()
            logger.debug("Service: Project found successfully.")
            return ResponseBuilder.build_response(200, {"message": "Success", "data": project_dict})
        except Exception as e:
            logger.error("Service: Error fetching project by id", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def get_projects_by_lead_id(cls, lead_id):
        """Retrieve all projects associated with a specific lead."""
        try:
            logger.debug(f"Service: get_projects_by_lead_id called with lead_id {lead_id}.")
            
            # Validate lead_id is an integer
            try:
                lead_id = int(lead_id)
            except (ValueError, TypeError):
                logger.error("Service: Provided lead_id is not a valid integer.")
                return ResponseBuilder.build_response(400, {"error": "Invalid lead ID"})

            with cls.db_util.session_scope() as session:
                projects = session.query(Project).filter(Project.lead_id == lead_id).all()
                project_list = [project.to_dict() for project in projects]
            logger.debug(f"Service: Retrieved {len(project_list)} projects for lead_id {lead_id}.")
            return ResponseBuilder.build_response(200, {"message": "Success", "data": project_list})
        except Exception as e:
            logger.error("Service: Error fetching projects by lead_id", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def advanced_search_projects(cls, search_text=None, filters=None, page=1, limit=10, sort_by="project_name", sort_order="asc"):
        """
        Perform advanced search on projects using the SearchUtility.
        
        Args:
            search_text: Global text search across project_name, project_description, lead_full_name
            filters: Dictionary of advanced filters with operators
                    Example: {
                        "lead_id": {"operator": "equals", "value": 69},
                        "project_name": {"operator": "contains", "value": "API"},
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
            logger.debug(f"Service: advanced_search_projects called with search_text='{search_text}', filters={filters}")
            
            with cls.db_util.session_scope() as session:
                # Use SearchUtility for advanced search
                search_result = SearchUtility.advanced_search(
                    session=session,
                    model=Project,
                    search_text=search_text,
                    search_columns=ModelSearchConfig.get_default_search_columns("Project"),
                    filters=filters,
                    page=page,
                    limit=limit,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                
                # Convert results to dictionaries
                project_list = [project.to_dict() for project in search_result["results"]]
                
                # Build response with pagination metadata
                response_data = {
                    "message": "Search completed successfully",
                    "data": project_list,
                    "total_count": search_result["total_count"],
                    "page": search_result["page"],
                    "limit": search_result["limit"],
                    "total_pages": search_result["total_pages"],
                    "has_next": search_result["has_next"],
                    "has_prev": search_result["has_prev"],
                    "search_metadata": {
                        "search_text": search_result["search_text"],
                        "filters_applied": search_result["filters_applied"],
                        "searchable_columns": ModelSearchConfig.get_searchable_columns("Project")
                    }
                }
                
            logger.debug(f"Service: Advanced search completed - {len(project_list)} results found")
            return ResponseBuilder.build_response(200, response_data)
            
        except Exception as e:
            logger.error("Service: Error in advanced_search_projects", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def create_project(cls, event: dict):
        """Create a new project."""
        try:
            if "body" not in event:
                logger.debug("Missing request body")
                return ResponseBuilder.build_response(400, {"error": "Missing request body"})

            try:
                project_data = json.loads(event["body"])
            except json.JSONDecodeError:
                logger.debug("Invalid JSON format")
                return ResponseBuilder.build_response(400, {"error": "Invalid JSON format"})

            if not isinstance(project_data, dict):
                logger.debug("Request body must be a JSON object")
                return ResponseBuilder.build_response(400, {"error": "Request body must be a JSON object"})

            logger.debug(f"Event received: {event}")
            logger.debug(f"Parsed project data: {project_data}")

            required_fields = ["lead_id", "project_name"]
            if not all(field in project_data for field in required_fields):
                logger.debug(f"Missing required fields: {required_fields}")
                return ResponseBuilder.build_response(400, {"error": "Missing required fields: lead_id, project_name"})

            # Validate lead_id is an integer
            try:
                lead_id = int(project_data["lead_id"])
                project_data["lead_id"] = lead_id
            except (ValueError, TypeError):
                logger.error("Service: Provided lead_id is not a valid integer.")
                return ResponseBuilder.build_response(400, {"error": "lead_id must be a valid integer"})

            # If lead_full_name is not provided, get it from leads table
            if 'lead_full_name' not in project_data:
                lead_full_name = Project.get_lead_full_name(lead_id)
                if lead_full_name:
                    project_data['lead_full_name'] = lead_full_name

            new_project = Project(**project_data)

            # Use the db_util instance to manage the session
            with cls.db_util.session_scope() as session:
                session.add(new_project)
                session.commit()
                session.refresh(new_project)  # Refresh to get the auto-generated ID

                return ResponseBuilder.build_response(201, {
                    "message": "Project created successfully",
                    "data": new_project.to_dict()
                })

        except Exception as e:
            logger.error("Service: Error creating project", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def update_project(cls, project_id: int, event: dict):
        """Update an existing project."""
        try:
            if "body" not in event:
                logger.debug("Missing request body")
                return ResponseBuilder.build_response(400, {"error": "Missing request body"})

            try:
                project_data = json.loads(event["body"])
            except json.JSONDecodeError:
                logger.debug("Invalid JSON format")
                return ResponseBuilder.build_response(400, {"error": "Invalid JSON format"})

            if not isinstance(project_data, dict):
                logger.debug("Request body must be a JSON object")
                return ResponseBuilder.build_response(400, {"error": "Request body must be a JSON object"})

            logger.debug(f"Service: update_project called with id {project_id} and data {project_data}")

            # Validate lead_id if provided
            if 'lead_id' in project_data:
                try:
                    lead_id = int(project_data["lead_id"])
                    project_data["lead_id"] = lead_id
                    # If lead_id is being updated, also update the lead_full_name
                    if 'lead_full_name' not in project_data:
                        lead_full_name = Project.get_lead_full_name(lead_id)
                        if lead_full_name:
                            project_data['lead_full_name'] = lead_full_name
                except (ValueError, TypeError):
                    logger.error("Service: Provided lead_id is not a valid integer.")
                    return ResponseBuilder.build_response(400, {"error": "lead_id must be a valid integer"})

            with cls.db_util.session_scope() as session:
                project = cls.dao.fetch_by_id(session, Project, project_id)
                if not project:
                    return ResponseBuilder.build_response(404, {"error": "Project not found"})

                # Update fields
                for key, value in project_data.items():
                    if hasattr(project, key):
                        setattr(project, key, value)

                session.commit()
                session.refresh(project)

                return ResponseBuilder.build_response(200, {
                    "message": "Project updated successfully",
                    "data": project.to_dict()
                })

        except Exception as e:
            logger.error("Service: Error updating project", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def delete_project(cls, project_id: int):
        """Delete a project."""
        try:
            logger.debug(f"Service: delete_project called with id {project_id}")

            with cls.db_util.session_scope() as session:
                project = cls.dao.fetch_by_id(session, Project, project_id)
                if not project:
                    return ResponseBuilder.build_response(404, {"error": "Project not found"})

                session.delete(project)
                session.commit()

                return ResponseBuilder.build_response(200, {
                    "message": "Project deleted successfully"
                })

        except Exception as e:
            logger.error("Service: Error deleting project", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})
