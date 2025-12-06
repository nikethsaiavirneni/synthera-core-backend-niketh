# ================================
# Add project root to sys.path
# ================================
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import uuid

# ================================
# Project-specific imports
# ================================
import logging
from com.dimcon.synthera.utilities.log_handler import LoggerManager
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility

# Import models
from com.dimcon.synthera.resources.tasks.task import Task

# ================================
# Tasks Service
# ================================
class TasksService:
    """
    Production-grade tasks service that handles task CRUD operations,
    assignments, status updates, and advanced filtering capabilities.
    """
    
    def __init__(self, cognito_utility: CognitoUserUtility):
        """
        Initialize TasksService with authentication utility.
        
        Args:
            cognito_utility: CognitoUserUtility instance for user authentication
        """
        self.cognito_utility = cognito_utility
        self.engine = get_engine()
        logger.info("TasksService initialized successfully")

    def list_tasks(self, event: dict, page: int = 1, limit: int = 50, 
                   sort_by: str = "created_date", sort_order: str = "desc",
                   search_text: Optional[str] = None, filters: Optional[Dict] = None) -> dict:
        """
        List tasks with pagination, sorting, and filtering.
        
        Args:
            event: API Gateway event
            page: Page number (1-based)
            limit: Number of items per page
            sort_by: Column to sort by
            sort_order: Sort order (asc/desc)
            search_text: Text to search in task title/description
            filters: Advanced filters dictionary
            
        Returns:
            Response with task list and metadata
        """
        logger.info(f"📋 Listing tasks - page: {page}, limit: {limit}, sort: {sort_by} {sort_order}")
        
        try:
            # Extract user context from event
            user_context = self.cognito_utility.extract_user_context_from_event(event)
            user_id = user_context["user_id"]
            org_id = user_context["org_id"]
            
            with DBSessionUtil() as session:
                # Start building the query
                query = session.query(Task).filter(Task.organization_id == org_id)
                
                # Apply search filter
                if search_text:
                    search_filter = f"%{search_text}%"
                    query = query.filter(
                        (Task.title.ilike(search_filter)) |
                        (Task.description.ilike(search_filter))
                    )
                
                # Apply advanced filters
                if filters:
                    for column_name, filter_config in filters.items():
                        operator = filter_config.get("operator", "equals")
                        value = filter_config.get("value")
                        
                        if hasattr(Task, column_name) and value is not None:
                            column = getattr(Task, column_name)
                            
                            if operator == "equals":
                                query = query.filter(column == value)
                            elif operator == "contains":
                                query = query.filter(column.ilike(f"%{value}%"))
                            elif operator == "gt":
                                query = query.filter(column > value)
                            elif operator == "lt":
                                query = query.filter(column < value)
                            elif operator == "gte":
                                query = query.filter(column >= value)
                            elif operator == "lte":
                                query = query.filter(column <= value)
                
                # Get total count
                total_count = query.count()
                
                # Apply sorting
                if hasattr(Task, sort_by):
                    sort_column = getattr(Task, sort_by)
                    if sort_order.lower() == "desc":
                        query = query.order_by(sort_column.desc())
                    else:
                        query = query.order_by(sort_column.asc())
                
                # Apply pagination
                offset = (page - 1) * limit
                tasks = query.offset(offset).limit(limit).all()
                
                # Convert to dictionaries
                tasks_data = []
                for task in tasks:
                    task_dict = {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "priority": task.priority,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "created_date": task.created_date.isoformat() if task.created_date else None,
                        "updated_date": task.updated_date.isoformat() if task.updated_date else None,
                        "created_by": task.created_by,
                        "assigned_to": task.assigned_to,
                        "organization_id": task.organization_id
                    }
                    tasks_data.append(task_dict)
                
                # Calculate pagination metadata
                total_pages = (total_count + limit - 1) // limit
                has_next = page < total_pages
                has_prev = page > 1
                
                result = {
                    "tasks": tasks_data,
                    "pagination": {
                        "current_page": page,
                        "total_pages": total_pages,
                        "total_count": total_count,
                        "page_size": limit,
                        "has_next": has_next,
                        "has_prev": has_prev
                    },
                    "filters_applied": {
                        "search": search_text,
                        "advanced_filters": filters or {},
                        "sort_by": sort_by,
                        "sort_order": sort_order
                    }
                }
                
                logger.info(f"✅ Successfully listed {len(tasks_data)} tasks")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error listing tasks: {str(e)}")
            logger.exception("Tasks listing error details:")
            return ResponseBuilder.build_response(500, {"error": "Failed to list tasks"})

    def get_task_by_id(self, task_id: str, event: dict) -> dict:
        """
        Get a specific task by ID.
        
        Args:
            task_id: Task ID
            event: API Gateway event
            
        Returns:
            Task data or error response
        """
        logger.info(f"📋 Getting task by ID: {task_id}")
        
        try:
            # Extract user context from event
            user_context = self.cognito_utility.extract_user_context_from_event(event)
            org_id = user_context["org_id"]
            
            with DBSessionUtil() as session:
                task = session.query(Task).filter(
                    Task.id == task_id,
                    Task.organization_id == org_id
                ).first()
                
                if not task:
                    logger.warning(f"Task not found: {task_id}")
                    return ResponseBuilder.build_response(404, {"error": "Task not found"})
                
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_date": task.created_date.isoformat() if task.created_date else None,
                    "updated_date": task.updated_date.isoformat() if task.updated_date else None,
                    "created_by": task.created_by,
                    "assigned_to": task.assigned_to,
                    "organization_id": task.organization_id
                }
                
                logger.info(f"✅ Successfully retrieved task: {task_id}")
                return task_data
                
        except Exception as e:
            logger.error(f"❌ Error getting task {task_id}: {str(e)}")
            logger.exception("Get task error details:")
            return ResponseBuilder.build_response(500, {"error": "Failed to get task"})

    def create_task(self, event: dict) -> dict:
        """
        Create a new task.
        
        Args:
            event: API Gateway event with task data in body
            
        Returns:
            Created task data or error response
        """
        logger.info("📝 Creating new task")
        
        try:
            # Extract user context from event
            user_context = self.cognito_utility.extract_user_context_from_event(event)
            user_id = user_context["user_id"]
            org_id = user_context["org_id"]
            
            # Parse request body
            request_body = json.loads(event.get("body", "{}"))
            
            # Validate required fields
            required_fields = ["title", "description"]
            missing_fields = [field for field in required_fields if field not in request_body]
            
            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                return ResponseBuilder.build_response(400, {
                    "error": "Missing required fields",
                    "missing_fields": missing_fields
                })
            
            with DBSessionUtil() as session:
                # Create new task
                new_task = Task(
                    id=str(uuid.uuid4()),
                    title=request_body["title"],
                    description=request_body["description"],
                    status=request_body.get("status", "pending"),
                    priority=request_body.get("priority", "medium"),
                    due_date=datetime.fromisoformat(request_body["due_date"]) if request_body.get("due_date") else None,
                    created_by=user_id,
                    assigned_to=request_body.get("assigned_to", user_id),
                    organization_id=org_id,
                    created_date=datetime.utcnow(),
                    updated_date=datetime.utcnow()
                )
                
                session.add(new_task)
                session.commit()
                
                task_data = {
                    "id": new_task.id,
                    "title": new_task.title,
                    "description": new_task.description,
                    "status": new_task.status,
                    "priority": new_task.priority,
                    "due_date": new_task.due_date.isoformat() if new_task.due_date else None,
                    "created_date": new_task.created_date.isoformat(),
                    "updated_date": new_task.updated_date.isoformat(),
                    "created_by": new_task.created_by,
                    "assigned_to": new_task.assigned_to,
                    "organization_id": new_task.organization_id
                }
                
                logger.info(f"✅ Successfully created task: {new_task.id}")
                return ResponseBuilder.build_response(201, {
                    "message": "Task created successfully",
                    "task": task_data
                })
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {str(e)}")
            return ResponseBuilder.build_response(400, {"error": "Invalid JSON in request body"})
        except Exception as e:
            logger.error(f"❌ Error creating task: {str(e)}")
            logger.exception("Create task error details:")
            return ResponseBuilder.build_response(500, {"error": "Failed to create task"})

    def update_task(self, task_id: str, event: dict) -> dict:
        """
        Update an existing task.
        
        Args:
            task_id: Task ID to update
            event: API Gateway event with update data in body
            
        Returns:
            Updated task data or error response
        """
        logger.info(f"📝 Updating task: {task_id}")
        
        # TODO: Implement task update functionality
        return ResponseBuilder.build_response(501, {
            "error": "Task update not yet implemented",
            "task_id": task_id
        })

    def delete_task(self, task_id: str, event: dict) -> dict:
        """
        Delete a task.
        
        Args:
            task_id: Task ID to delete
            event: API Gateway event
            
        Returns:
            Success response or error response
        """
        logger.info(f"🗑️ Deleting task: {task_id}")
        
        # TODO: Implement task deletion functionality
        return ResponseBuilder.build_response(501, {
            "error": "Task deletion not yet implemented",
            "task_id": task_id
        })

    def get_assigned_tasks(self, event: dict, page: int = 1, limit: int = 50,
                          sort_by: str = "created_date", sort_order: str = "desc",
                          search_text: Optional[str] = None, filters: Optional[Dict] = None) -> dict:
        """
        Get tasks assigned to the current user.
        
        Args:
            event: API Gateway event
            page: Page number
            limit: Items per page
            sort_by: Sort column
            sort_order: Sort order
            search_text: Search text
            filters: Advanced filters
            
        Returns:
            Assigned tasks list
        """
        logger.info("👤 Getting assigned tasks")
        
        try:
            # Extract user context from event
            user_context = self.cognito_utility.extract_user_context_from_event(event)
            user_id = user_context["user_id"]
            
            # Add assigned_to filter
            if not filters:
                filters = {}
            filters["assigned_to"] = {"operator": "equals", "value": user_id}
            
            return self.list_tasks(event, page, limit, sort_by, sort_order, search_text, filters)
            
        except Exception as e:
            logger.error(f"❌ Error getting assigned tasks: {str(e)}")
            return ResponseBuilder.build_response(500, {"error": "Failed to get assigned tasks"})

    def get_created_tasks(self, event: dict, page: int = 1, limit: int = 50,
                         sort_by: str = "created_date", sort_order: str = "desc",
                         search_text: Optional[str] = None, filters: Optional[Dict] = None) -> dict:
        """
        Get tasks created by the current user.
        
        Args:
            event: API Gateway event
            page: Page number
            limit: Items per page
            sort_by: Sort column
            sort_order: Sort order
            search_text: Search text
            filters: Advanced filters
            
        Returns:
            Created tasks list
        """
        logger.info("✏️ Getting created tasks")
        
        try:
            # Extract user context from event
            user_context = self.cognito_utility.extract_user_context_from_event(event)
            user_id = user_context["user_id"]
            
            # Add created_by filter
            if not filters:
                filters = {}
            filters["created_by"] = {"operator": "equals", "value": user_id}
            
            return self.list_tasks(event, page, limit, sort_by, sort_order, search_text, filters)
            
        except Exception as e:
            logger.error(f"❌ Error getting created tasks: {str(e)}")
            return ResponseBuilder.build_response(500, {"error": "Failed to get created tasks"})

    def get_overdue_tasks(self, event: dict, page: int = 1, limit: int = 50,
                         sort_by: str = "due_date", sort_order: str = "asc",
                         search_text: Optional[str] = None, filters: Optional[Dict] = None) -> dict:
        """
        Get overdue tasks.
        
        Args:
            event: API Gateway event
            page: Page number
            limit: Items per page
            sort_by: Sort column
            sort_order: Sort order
            search_text: Search text
            filters: Advanced filters
            
        Returns:
            Overdue tasks list
        """
        logger.info("⏰ Getting overdue tasks")
        
        try:
            # Add overdue filter (due_date < current date and status != completed)
            if not filters:
                filters = {}
            
            current_date = datetime.utcnow().isoformat()
            filters["due_date"] = {"operator": "lt", "value": current_date}
            filters["status"] = {"operator": "not_equals", "value": "completed"}
            
            return self.list_tasks(event, page, limit, sort_by, sort_order, search_text, filters)
            
        except Exception as e:
            logger.error(f"❌ Error getting overdue tasks: {str(e)}")
            return ResponseBuilder.build_response(500, {"error": "Failed to get overdue tasks"})

    def get_completed_tasks(self, event: dict, page: int = 1, limit: int = 50,
                           sort_by: str = "updated_date", sort_order: str = "desc",
                           search_text: Optional[str] = None, filters: Optional[Dict] = None) -> dict:
        """
        Get completed tasks.
        
        Args:
            event: API Gateway event
            page: Page number
            limit: Items per page
            sort_by: Sort column
            sort_order: Sort order
            search_text: Search text
            filters: Advanced filters
            
        Returns:
            Completed tasks list
        """
        logger.info("✅ Getting completed tasks")
        
        try:
            # Add completed status filter
            if not filters:
                filters = {}
            filters["status"] = {"operator": "equals", "value": "completed"}
            
            return self.list_tasks(event, page, limit, sort_by, sort_order, search_text, filters)
            
        except Exception as e:
            logger.error(f"❌ Error getting completed tasks: {str(e)}")
            return ResponseBuilder.build_response(500, {"error": "Failed to get completed tasks"})

    def assign_task(self, event: dict) -> dict:
        """
        Assign a task to a user.
        
        Args:
            event: API Gateway event with assignment data
            
        Returns:
            Success response or error response
        """
        logger.info("👤 Assigning task")
        
        # TODO: Implement task assignment functionality
        return ResponseBuilder.build_response(501, {"error": "Task assignment not yet implemented"})

    def update_task_status(self, task_id: str, event: dict) -> dict:
        """
        Update task status.
        
        Args:
            task_id: Task ID
            event: API Gateway event with status data
            
        Returns:
            Updated task or error response
        """
        logger.info(f"🔄 Updating task status: {task_id}")
        
        # TODO: Implement task status update functionality
        return ResponseBuilder.build_response(501, {
            "error": "Task status update not yet implemented",
            "task_id": task_id
        })

    def complete_task(self, task_id: str, event: dict) -> dict:
        """
        Mark task as completed.
        
        Args:
            task_id: Task ID
            event: API Gateway event
            
        Returns:
            Updated task or error response
        """
        logger.info(f"✅ Completing task: {task_id}")
        
        # TODO: Implement task completion functionality
        return ResponseBuilder.build_response(501, {
            "error": "Task completion not yet implemented", 
            "task_id": task_id
        })

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    logger.info("Testing TasksService")
    
    # This would be used for standalone testing
    # Mock event for testing
    test_event = {
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user-id",
                    "email": "test@example.com"
                }
            }
        },
        "body": json.dumps({
            "title": "Test Task",
            "description": "This is a test task"
        })
    }
    
    try:
        # Initialize with mock cognito utility for testing
        from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility
        cognito_utility = CognitoUserUtility()
        service = TasksService(cognito_utility)
        logger.info("TasksService test initialization successful")
    except Exception as e:
        logger.error(f"TasksService test failed: {e}")
