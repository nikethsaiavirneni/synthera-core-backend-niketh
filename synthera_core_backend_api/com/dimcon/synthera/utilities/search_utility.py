"""
Advanced Search Utility for Synthera Core Backend API

This utility provides comprehensive search functionality that can be used across
all modules (projects, leads, meetings, etc.) for flexible data querying.

Features:
- Multi-column text search
- Advanced filtering with multiple operators
- Date range filtering
- Numeric range filtering 
- Case-insensitive search
- Pagination and sorting
- Configurable search fields per model

Usage:
    from com.dimcon.synthera.utilities.search_utility import SearchUtility
    
    # Simple text search
    results = SearchUtility.advanced_search(
        session, MyModel, 
        search_text="john", 
        search_columns=["first_name", "last_name", "email"]
    )
    
    # Advanced filtering
    results = SearchUtility.advanced_search(
        session, MyModel,
        filters={
            "status": {"operator": "equals", "value": "active"},
            "age": {"operator": "greater_than", "value": 18},
            "created_at": {"operator": "date_range", "start": "2025-01-01", "end": "2025-12-31"}
        }
    )
"""

import os
import sys
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
import logging

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import and_, or_, text, func, Integer, String, DateTime, Date, Numeric, Boolean, TIMESTAMP
from sqlalchemy.orm import Session
from sqlalchemy.sql import operators
from sqlalchemy.inspection import inspect

from com.dimcon.synthera.utilities.log_handler import LoggerManager

logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)


class SearchOperators:
    """Define available search operators for advanced filtering."""
    
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    GREATER_THAN_EQUAL = "greater_than_equal"
    LESS_THAN = "less_than"
    LESS_THAN_EQUAL = "less_than_equal"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    DATE_RANGE = "date_range"
    NUMERIC_RANGE = "numeric_range"
    REGEX = "regex"


class SearchUtility:
    """
    Advanced search utility providing flexible search and filtering capabilities
    across any SQLAlchemy model.
    """
    
    @staticmethod
    def get_model_searchable_columns(model) -> Dict[str, str]:
        """
        Get searchable columns for a model with their data types.
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            Dict mapping column names to their SQLAlchemy types
        """
        inspector = inspect(model)
        columns = {}
        
        for column in inspector.columns:
            column_type = type(column.type).__name__
            columns[column.name] = column_type
            
        logger.debug(f"Searchable columns for {model.__name__}: {columns}")
        return columns
    
    @staticmethod
    def build_text_search_filter(model, search_text: str, search_columns: List[str]):
        """
        Build a filter for text search across multiple columns.
        
        Args:
            model: SQLAlchemy model class
            search_text: Text to search for
            search_columns: List of column names to search in
            
        Returns:
            SQLAlchemy filter condition
        """
        if not search_text or not search_columns:
            return None
            
        search_conditions = []
        search_text = f"%{search_text.lower()}%"
        
        for column_name in search_columns:
            column = getattr(model, column_name, None)
            if column is not None:
                # Use case-insensitive search
                search_conditions.append(func.lower(column).like(search_text))
            else:
                logger.warning(f"Column '{column_name}' not found in model {model.__name__}")
        
        if search_conditions:
            return or_(*search_conditions)
        return None
    
    @staticmethod
    def build_advanced_filter(model, column_name: str, filter_config: Dict[str, Any]):
        """
        Build advanced filter condition based on operator and value.
        
        Args:
            model: SQLAlchemy model class
            column_name: Name of the column to filter
            filter_config: Dictionary containing operator and value(s)
                          Example: {"operator": "contains", "value": "john"}
                          
        Returns:
            SQLAlchemy filter condition
        """
        column = getattr(model, column_name, None)
        if column is None:
            logger.warning(f"Column '{column_name}' not found in model {model.__name__}")
            return None
            
        operator = filter_config.get("operator", SearchOperators.EQUALS)
        value = filter_config.get("value")
        
        try:
            if operator == SearchOperators.EQUALS:
                return column == value
                
            elif operator == SearchOperators.NOT_EQUALS:
                return column != value
                
            elif operator == SearchOperators.CONTAINS:
                if isinstance(value, str):
                    return func.lower(column).like(f"%{value.lower()}%")
                return column.like(f"%{value}%")
                
            elif operator == SearchOperators.NOT_CONTAINS:
                if isinstance(value, str):
                    return ~func.lower(column).like(f"%{value.lower()}%")
                return ~column.like(f"%{value}%")
                
            elif operator == SearchOperators.STARTS_WITH:
                if isinstance(value, str):
                    return func.lower(column).like(f"{value.lower()}%")
                return column.like(f"{value}%")
                
            elif operator == SearchOperators.ENDS_WITH:
                if isinstance(value, str):
                    return func.lower(column).like(f"%{value.lower()}")
                return column.like(f"%{value}")
                
            elif operator == SearchOperators.GREATER_THAN:
                return column > value
                
            elif operator == SearchOperators.GREATER_THAN_EQUAL:
                return column >= value
                
            elif operator == SearchOperators.LESS_THAN:
                return column < value
                
            elif operator == SearchOperators.LESS_THAN_EQUAL:
                return column <= value
                
            elif operator == SearchOperators.IN:
                if isinstance(value, (list, tuple)):
                    return column.in_(value)
                return column == value
                
            elif operator == SearchOperators.NOT_IN:
                if isinstance(value, (list, tuple)):
                    return ~column.in_(value)
                return column != value
                
            elif operator == SearchOperators.IS_NULL:
                return column.is_(None)
                
            elif operator == SearchOperators.IS_NOT_NULL:
                return column.is_not(None)
                
            elif operator == SearchOperators.DATE_RANGE:
                start_date = filter_config.get("start")
                end_date = filter_config.get("end")
                conditions = []
                
                if start_date:
                    if isinstance(start_date, str):
                        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    conditions.append(column >= start_date)
                    
                if end_date:
                    if isinstance(end_date, str):
                        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    conditions.append(column <= end_date)
                    
                return and_(*conditions) if conditions else None
                
            elif operator == SearchOperators.NUMERIC_RANGE:
                min_value = filter_config.get("min")
                max_value = filter_config.get("max")
                conditions = []
                
                if min_value is not None:
                    conditions.append(column >= min_value)
                if max_value is not None:
                    conditions.append(column <= max_value)
                    
                return and_(*conditions) if conditions else None
                
            elif operator == SearchOperators.REGEX:
                # PostgreSQL regex operator
                return column.op('~*')(value)  # Case-insensitive regex
                
            else:
                logger.warning(f"Unknown search operator: {operator}")
                return None
                
        except Exception as e:
            logger.error(f"Error building filter for column '{column_name}' with operator '{operator}': {e}")
            return None
    
    @staticmethod
    def advanced_search(
        session: Session,
        model,
        search_text: Optional[str] = None,
        search_columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
        page: int = 1,
        limit: int = 10,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Perform advanced search with text search, filtering, pagination, and sorting.
        
        Args:
            session: SQLAlchemy session
            model: SQLAlchemy model class
            search_text: Global text to search for across search_columns
            search_columns: List of column names to search in for text search
            filters: Dictionary of filters with simple values or advanced filter configs
                    Example: {
                        "status": "active",  # Simple filter
                        "age": {"operator": "greater_than", "value": 18},  # Advanced filter
                        "created_at": {"operator": "date_range", "start": "2025-01-01", "end": "2025-12-31"}
                    }
            page: Page number for pagination
            limit: Number of records per page
            sort_by: Column name to sort by
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.debug(f"Advanced search on {model.__name__}: text='{search_text}', filters={filters}")
            
            # Start with base query
            query = session.query(model)
            filter_conditions = []
            
            # Add text search filter
            if search_text and search_columns:
                text_filter = SearchUtility.build_text_search_filter(model, search_text, search_columns)
                if text_filter is not None:
                    filter_conditions.append(text_filter)
            
            # Add advanced filters
            if filters:
                for column_name, filter_value in filters.items():
                    if isinstance(filter_value, dict):
                        # Advanced filter with operator
                        filter_condition = SearchUtility.build_advanced_filter(model, column_name, filter_value)
                    else:
                        # Simple filter - treat as equals
                        filter_condition = SearchUtility.build_advanced_filter(
                            model, column_name, {"operator": SearchOperators.EQUALS, "value": filter_value}
                        )
                    
                    if filter_condition is not None:
                        filter_conditions.append(filter_condition)
            
            # Apply all filters
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            if sort_by:
                sort_column = getattr(model, sort_by, None)
                if sort_column is not None:
                    if sort_order.lower() == "desc":
                        query = query.order_by(sort_column.desc())
                    else:
                        query = query.order_by(sort_column.asc())
                else:
                    logger.warning(f"Sort column '{sort_by}' not found in {model.__name__}")
            
            # Apply pagination
            offset = (page - 1) * limit
            results = query.offset(offset).limit(limit).all()
            
            # Calculate pagination metadata
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            logger.debug(f"Search completed: {len(results)} results, {total_count} total")
            
            return {
                "results": results,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "search_text": search_text,
                "filters_applied": len(filter_conditions) > 0
            }
            
        except Exception as e:
            logger.error(f"Error in advanced_search: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_default_search_columns(model) -> List[str]:
        """
        Get default searchable columns for a model (typically text/string columns).
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            List of column names suitable for text search
        """
        searchable_columns = []
        inspector = inspect(model)
        
        for column in inspector.columns:
            # Include string columns and commonly searchable types
            if isinstance(column.type, (String,)):
                # Exclude certain system columns
                if not column.name.endswith(('_id', '_at')) and column.name not in ['password', 'hash', 'token']:
                    searchable_columns.append(column.name)
        
        logger.debug(f"Default search columns for {model.__name__}: {searchable_columns}")
        return searchable_columns


class ModelSearchConfig:
    """
    Configuration class for defining search behavior for specific models.
    """
    
    # Define search configurations for each model
    CONFIGS = {
        "Project": {
            "default_search_columns": ["project_name", "project_description", "lead_full_name"],
            "searchable_columns": ["project_name", "project_description", "lead_full_name", "s3_url_transcription", "s3_url_sow_ppt"],
            "filterable_columns": ["lead_id", "project_name", "lead_full_name", "created_at", "updated_at"],
            "default_sort": "project_name"
        },
        "LeadDetail": {
            "default_search_columns": ["lead_first_name", "lead_last_name", "lead_email", "lead_company_name"],
            "searchable_columns": ["lead_first_name", "lead_last_name", "lead_email", "lead_company_name", "lead_phone_number", "lead_address"],
            "filterable_columns": ["lead_first_name", "lead_last_name", "lead_email", "lead_company_name", "lead_status", "created_at"],
            "default_sort": "lead_first_name"
        },
        "Meeting": {
            "default_search_columns": ["meeting_name", "meeting_description", "meeting_location"],
            "searchable_columns": ["meeting_name", "meeting_description", "meeting_location"],
            "filterable_columns": ["meeting_name", "meeting_status", "meeting_date", "created_at"],
            "default_sort": "meeting_date"
        }
    }
    
    @classmethod
    def get_config(cls, model_name: str) -> Dict[str, Any]:
        """Get search configuration for a specific model."""
        return cls.CONFIGS.get(model_name, {
            "default_search_columns": [],
            "searchable_columns": [],
            "filterable_columns": [],
            "default_sort": "id"
        })
    
    @classmethod
    def get_default_search_columns(cls, model_name: str) -> List[str]:
        """Get default search columns for a model."""
        config = cls.get_config(model_name)
        return config.get("default_search_columns", [])
    
    @classmethod
    def get_searchable_columns(cls, model_name: str) -> List[str]:
        """Get all searchable columns for a model."""
        config = cls.get_config(model_name)
        return config.get("searchable_columns", [])
    
    @classmethod
    def get_filterable_columns(cls, model_name: str) -> List[str]:
        """Get filterable columns for a model."""
        config = cls.get_config(model_name)
        return config.get("filterable_columns", [])
    
    @classmethod
    def get_default_sort(cls, model_name: str) -> str:
        """Get default sort column for a model."""
        config = cls.get_config(model_name)
        return config.get("default_sort", "id")


# Convenience functions for easy usage
def search_projects(session: Session, search_text: str = None, **filters) -> Dict[str, Any]:
    """Convenience function for searching projects."""
    from com.dimcon.synthera.resources.projects.projects_lead import Project
    
    return SearchUtility.advanced_search(
        session=session,
        model=Project,
        search_text=search_text,
        search_columns=ModelSearchConfig.get_default_search_columns("Project"),
        filters=filters,
        sort_by=ModelSearchConfig.get_default_sort("Project")
    )


def search_leads(session: Session, search_text: str = None, **filters) -> Dict[str, Any]:
    """Convenience function for searching leads."""
    from com.dimcon.synthera.resources.leads.leads_details import LeadDetail
    
    return SearchUtility.advanced_search(
        session=session,
        model=LeadDetail,
        search_text=search_text,
        search_columns=ModelSearchConfig.get_default_search_columns("LeadDetail"),
        filters=filters,
        sort_by=ModelSearchConfig.get_default_sort("LeadDetail")
    )


def search_meetings(session: Session, search_text: str = None, **filters) -> Dict[str, Any]:
    """Convenience function for searching meetings."""
    # Note: Import when needed to avoid circular imports
    try:
        from com.dimcon.synthera.resources.meeting.meeting import Meeting
        return SearchUtility.advanced_search(
            session=session,
            model=Meeting,
            search_text=search_text,
            search_columns=ModelSearchConfig.get_default_search_columns("Meeting"),
            filters=filters,
            sort_by=ModelSearchConfig.get_default_sort("Meeting")
        )
    except ImportError:
        logger.warning("Meeting model not available for search")
        return {"results": [], "total_count": 0}


if __name__ == "__main__":
    """
    Test script for the search utility.
    """
    print("🔍 Search Utility Test")
    print("=" * 50)
    
    # Test model introspection
    try:
        from com.dimcon.synthera.resources.projects.projects_lead import Project
        columns = SearchUtility.get_model_searchable_columns(Project)
        print(f"Project searchable columns: {columns}")
        
        default_search = ModelSearchConfig.get_default_search_columns("Project")
        print(f"Default search columns: {default_search}")
        
    except Exception as e:
        print(f"Error in test: {e}")
