# ================================
# Add project root to sys.path
# ================================
import os
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add the current working directory if we're running directly
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ================================
# Standard library imports
# ================================
from datetime import datetime, UTC

# ================================
# Third-party imports
# ================================
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, inspect
from sqlalchemy.orm import relationship, Session

# ================================
# Centralized Logger and Database Utilities
# ================================
from com.dimcon.synthera.utilities.log_handler import LoggerManager
import logging
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.s3_utility import generate_download_url, is_valid_s3_key

# Create engine using the centralized connection utility and instantiate session management.
engine = get_engine()
db_util = DBSessionUtil(engine)

# ================================
# Project-specific imports
# ================================
from com.dimcon.synthera.resources.base import Base
from com.dimcon.synthera.resources.leads.leads_details import LeadDetail

# Clear any existing table definitions to avoid conflicts
if hasattr(Base.metadata, 'tables') and 'project_leads' in Base.metadata.tables:
    Base.metadata.remove(Base.metadata.tables['project_leads'])

# ================================
# Model Definition
# ================================
class Project(Base):
    __tablename__ = "project_leads"
    __table_args__ = {'extend_existing': True}

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads_details.lead_id"), nullable=False)
    project_name = Column(String(255), nullable=False)
    project_description = Column(String(1000))  # New column for project description
    lead_full_name = Column(String(255))  # Denormalized lead name for performance
    s3_url_transcription = Column(String(500))
    s3_url_sow_ppt = Column(String(500))
    s3_url_ai_json = Column(String(500))  # New column for AI-generated JSON file path
    # Store cognito_sub of the employee who created/updated this project
    created_by = Column(String(255), ForeignKey("employees.cognito_sub"), nullable=True)
    updated_by = Column(String(255), ForeignKey("employees.cognito_sub"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # Define relationship to leads_details table (optional, for when you need other lead details)
    lead_detail = relationship("LeadDetail", foreign_keys=[lead_id])

    @classmethod
    def get_lead_full_name(cls, lead_id: int):
        """
        Helper method to get the full lead name from leads_details table.
        This can be used when creating or updating projects to populate lead_full_name.
        """
        with db_util.session_scope() as session:
            lead = session.query(LeadDetail).filter(LeadDetail.lead_id == lead_id).first()
            if lead:
                return f"{lead.lead_first_name} {lead.lead_last_name}"
            return None

    @classmethod
    def create_table(cls, engine):
        """
        Creates the project_leads table if it doesn't exist.
        """
        inspector = inspect(engine)
        if cls.__tablename__ not in inspector.get_table_names():
            cls.__table__.create(bind=engine)
            logger.info("Table 'project_leads' created.")
        else:
            logger.info("Table 'project_leads' already exists. Skipping creation.")

    @classmethod
    def drop_table(cls, engine):
        """
        Drops the project_leads table.
        """
        cls.__table__.drop(bind=engine, checkfirst=True)
        logger.info("Table 'project_leads' dropped.")

    @classmethod
    def insert_table(cls, **kwargs):
        """
        Inserts a new project record using a managed session.
        Automatically populates lead_full_name from the leads_details table.
        """
        # If lead_full_name is not provided, get it from leads table
        if 'lead_full_name' not in kwargs and 'lead_id' in kwargs:
            lead_full_name = cls.get_lead_full_name(kwargs['lead_id'])
            if lead_full_name:
                kwargs['lead_full_name'] = lead_full_name
        
        new_project = cls(**kwargs)
        with db_util.session_scope() as session:
            session.add(new_project)
            session.commit()
            logger.info(f"Project '{new_project.project_name}' inserted successfully.")
            return new_project.project_id

    @classmethod
    def get_by_id(cls, project_id: int):
        """
        Retrieves a project by its ID.
        Returns a detached object safe for use outside session.
        """
        with db_util.session_scope() as session:
            project = session.query(cls).filter(cls.project_id == project_id).first()
            if project:
                # Access all attributes to load them before session closes
                _ = project.project_id
                _ = project.lead_id
                _ = project.project_name
                _ = project.project_description
                _ = project.lead_full_name
                _ = project.s3_url_transcription
                _ = project.s3_url_sow_ppt
                _ = project.s3_url_ai_json
                _ = project.created_by
                _ = project.updated_by
                _ = project.created_at
                _ = project.updated_at
                session.expunge(project)  # Detach from session
            return project

    @classmethod
    def get_by_lead_id(cls, lead_id: int):
        """
        Retrieves all projects associated with a specific lead.
        """
        with db_util.session_scope() as session:
            projects = session.query(cls).filter(cls.lead_id == lead_id).all()
            return projects

    @classmethod
    def get_all(cls):
        """
        Retrieves all projects.
        """
        with db_util.session_scope() as session:
            projects = session.query(cls).all()
            return projects

    @classmethod
    def update_project(cls, project_id: int, **kwargs):
        """
        Updates a project record.
        If lead_id is being updated, automatically updates lead_full_name as well.
        """
        with db_util.session_scope() as session:
            project = session.query(cls).filter(cls.project_id == project_id).first()
            if project:
                # If lead_id is being updated, also update the lead_full_name
                if 'lead_id' in kwargs and 'lead_full_name' not in kwargs:
                    new_lead_full_name = cls.get_lead_full_name(kwargs['lead_id'])
                    if new_lead_full_name:
                        kwargs['lead_full_name'] = new_lead_full_name
                
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                project.updated_at = datetime.now(UTC)
                session.commit()
                logger.info(f"Project ID {project_id} updated successfully.")
                return project
            else:
                logger.warning(f"Project ID {project_id} not found.")
                return None

    @classmethod
    def delete_project(cls, project_id: int):
        """
        Deletes a project record.
        """
        with db_util.session_scope() as session:
            project = session.query(cls).filter(cls.project_id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                logger.info(f"Project ID {project_id} deleted successfully.")
                return True
            else:
                logger.warning(f"Project ID {project_id} not found.")
                return False

    def to_dict(self, include_download_urls: bool = True):
        """
        Converts the project instance to a dictionary.
        
        Args:
            include_download_urls (bool): Whether to generate pre-signed download URLs.
                                        Defaults to True for API responses.
        
        Returns:
            dict: Project data with optional download URLs
        """
        base_dict = {
            "project_id": self.project_id,
            "lead_id": self.lead_id,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "lead_full_name": self.lead_full_name,  # Direct column access, no join needed
            "s3_url_transcription": self.s3_url_transcription,
            "s3_url_sow_ppt": self.s3_url_sow_ppt,
            "s3_url_ai_json": self.s3_url_ai_json,  # New AI JSON file path
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Add secure download URLs if requested
        if include_download_urls:
            # Generate pre-signed URL for SOW PowerPoint if available
            if self.s3_url_sow_ppt and self.s3_url_sow_ppt.strip():
                try:
                    logger.debug("🔗 Generating download URL for SOW PPT: %s", self.s3_url_sow_ppt)
                    if is_valid_s3_key(self.s3_url_sow_ppt):
                        download_url = generate_download_url(self.s3_url_sow_ppt, expiration_hours=1)
                        if download_url:
                            base_dict["sow_ppt_download_url"] = download_url
                            logger.debug("✅ SOW PPT download URL generated successfully")
                        else:
                            logger.warning("⚠️ Failed to generate download URL for SOW PPT")
                            base_dict["sow_ppt_download_url"] = None
                    else:
                        logger.warning("⚠️ SOW PPT S3 key is invalid or object doesn't exist")
                        base_dict["sow_ppt_download_url"] = None
                except Exception as e:
                    logger.error("❌ Error generating SOW PPT download URL: %s", str(e))
                    base_dict["sow_ppt_download_url"] = None
            else:
                # Don't include the field if no S3 key is available
                pass
            
            # Generate pre-signed URL for transcription if available
            if self.s3_url_transcription and self.s3_url_transcription.strip():
                try:
                    logger.debug("🔗 Generating download URL for transcription: %s", self.s3_url_transcription)
                    if is_valid_s3_key(self.s3_url_transcription):
                        download_url = generate_download_url(self.s3_url_transcription, expiration_hours=1)
                        if download_url:
                            base_dict["transcription_download_url"] = download_url
                            logger.debug("✅ Transcription download URL generated successfully")
                        else:
                            logger.warning("⚠️ Failed to generate download URL for transcription")
                            base_dict["transcription_download_url"] = None
                    else:
                        logger.warning("⚠️ Transcription S3 key is invalid or object doesn't exist")
                        base_dict["transcription_download_url"] = None
                except Exception as e:
                    logger.error("❌ Error generating transcription download URL: %s", str(e))
                    base_dict["transcription_download_url"] = None
            else:
                # Don't include the field if no S3 key is available
                pass
            
            # Generate pre-signed URL for AI JSON file if available
            if self.s3_url_ai_json and self.s3_url_ai_json.strip():
                try:
                    logger.debug("🔗 Generating download URL for AI JSON: %s", self.s3_url_ai_json)
                    if is_valid_s3_key(self.s3_url_ai_json):
                        download_url = generate_download_url(self.s3_url_ai_json, expiration_hours=1)
                        if download_url:
                            base_dict["ai_json_download_url"] = download_url
                            logger.debug("✅ AI JSON download URL generated successfully")
                        else:
                            logger.warning("⚠️ Failed to generate download URL for AI JSON")
                            base_dict["ai_json_download_url"] = None
                    else:
                        logger.warning("⚠️ AI JSON S3 key is invalid or object doesn't exist")
                        base_dict["ai_json_download_url"] = None
                except Exception as e:
                    logger.error("❌ Error generating AI JSON download URL: %s", str(e))
                    base_dict["ai_json_download_url"] = None
            else:
                # Don't include the field if no S3 key is available
                pass
        
        return base_dict

    def __repr__(self):
        """
        String representation of the Project instance.
        """
        return f"<Project(project_id={self.project_id}, project_name='{self.project_name}', lead_full_name='{self.lead_full_name}')>"


# ================================
# Main execution block for testing
# ================================
if __name__ == "__main__":
    """
    Main execution block for testing the Project model.
    This allows you to run the script directly to test functionality.
    """
    try:
        logger.info("Starting Project model test execution...")
        
        # Create the projects table
        Project.create_table(engine)
        
        # Test data using the provided lead information (lead_id: 69, niketh sai)
        test_project_data = {
            "lead_id": 69,  # Using the provided lead_id for niketh sai
            "project_name": "AI Integration Project - niketh sai",
            "project_description": "A comprehensive AI integration project focusing on machine learning capabilities and automated workflow optimization for improved business processes.",
            "s3_url_ai_json": "documents/projects/69/ai_analysis_niketh_sai.json"  # Sample AI JSON file path
        }
        
        # Insert the test project
        logger.info("Inserting test project for niketh sai...")
        project_id = Project.insert_table(**test_project_data)
        logger.info(f"Test project inserted with ID: {project_id}")
        
        # Retrieve the project by ID to verify
        logger.info("Retrieving project by ID...")
        project = Project.get_by_id(project_id)
        if project:
            logger.info(f"Retrieved project: {project}")
            logger.info(f"Project as dict: {project.to_dict()}")
        
        # Get all projects
        logger.info("Retrieving all projects...")
        all_projects = Project.get_all()
        logger.info(f"Total projects in database: {len(all_projects)}")
        
        logger.info("Project model test execution completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during Project model test execution: {str(e)}")
        raise
