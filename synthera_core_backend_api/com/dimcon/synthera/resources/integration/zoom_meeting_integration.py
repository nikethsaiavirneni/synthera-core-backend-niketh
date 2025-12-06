# ================================
# Add project root to sys.path
# ================================
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
import pytz
from datetime import datetime, UTC

# ================================
# Third-party imports
# ================================
from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, ForeignKey, inspect, Text
from sqlalchemy.orm import Session

# ================================
# Centralized Logger and Database Utilities
# ================================
from com.dimcon.synthera.utilities.log_handler import LoggerManager
import logging
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil


# Create engine and session manager
engine = get_engine()
db_util = DBSessionUtil(engine)

# ================================
# Project-specific imports
# ================================
from com.dimcon.synthera.resources.base import Base
from com.dimcon.synthera.resources.integration.status import Status
from com.dimcon.synthera.resources.integration.integration import Integration
from com.dimcon.synthera.resources.database_and_users.standard_user import StandardUser
from com.dimcon.synthera.resources.projects.projects_lead import Project

# ================================
# Model Definition
# ================================
class ZoomMeetingIntegration(Base):
    __tablename__ = 'zoom_meeting_integrations'

    meeting_id = Column(BigInteger, primary_key=True, autoincrement=True)
    host_url = Column(String)
    join_url = Column(String)
    start_url = Column(String)
    meeting_password = Column(String)
    meeting_topic = Column(String)
    meeting_agenda = Column(String)
    start_time = Column(TIMESTAMP(timezone=True))
    duration_minutes = Column(Integer)
    timezone = Column(String)
    status_id = Column(Integer, ForeignKey(Status.status_id))
    integration_id = Column(Integer, ForeignKey(Integration.integration_id))
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Link to user for meeting ownership
    app_user_id = Column(String(255), nullable=False)  # Your app's user ID (email) - for meeting ownership
    project_id = Column(Integer, ForeignKey("project_leads.project_id"), nullable=True)
    project_code = Column(String(100), nullable=True)  # <-- Add this line

    @classmethod
    def create_table(cls, engine):
        inspector = inspect(engine)
        if cls.__tablename__ not in inspector.get_table_names():
            cls.__table__.create(bind=engine)
            logger.info("Table 'zoom_meeting_integrations' created.")
        else:
            logger.info("Table 'zoom_meeting_integrations' already exists. Skipping creation.")

    @classmethod
    def drop_table(cls, engine):
        cls.__table__.drop(bind=engine, checkfirst=True)
        logger.info("Table 'zoom_meeting_integrations' dropped.")

    @classmethod
    def insert_table(cls, **kwargs):
        """
        Inserts a new Zoom meeting record and returns a dictionary.
        """
        new_meeting = cls(**kwargs)
        with db_util.session_scope() as session:
            session.add(new_meeting)
            session.flush()  # flush writes the record into DB immediately
            logger.info(f"Inserted Zoom meeting with ID: {new_meeting.meeting_id}")
            meeting_dict = new_meeting.to_dict()  # call to_dict inside session
        return meeting_dict  # return dictionary

    @classmethod
    def update_table(cls, meeting_id: str, **kwargs):
        """
        Updates an existing Zoom meeting record and returns updated dictionary.
        """
        with db_util.session_scope() as session:
            meeting = session.query(cls).filter_by(meeting_id=meeting_id).first()
            if meeting:
                for key, value in kwargs.items():
                    setattr(meeting, key, value)
                session.flush()
                logger.info(f"Updated Zoom meeting with ID: {meeting_id}")
                meeting_dict = meeting.to_dict()
            else:
                logger.warning(f"Meeting with ID {meeting_id} not found.")
                meeting_dict = None
        return meeting_dict

    @classmethod
    def get_table(cls, **filters):
        """
        Fetches Zoom meeting records matching the filters.
        """
        with db_util.session_scope() as session:
            meetings = session.query(cls).filter_by(**filters).all()
            meetings_dict = [meeting.to_dict() for meeting in meetings]
            logger.info(f"Fetched {len(meetings)} Zoom meeting(s) with filters: {filters}")
        return meetings_dict

    @classmethod
    def alter_table(cls):
        raise NotImplementedError("Use Alembic or raw SQL for altering tables.")

    def to_dict(self):
        """
        Convert the ORM object to a dictionary.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if hasattr(value, "isoformat"):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    # Create table if not exists
    ZoomMeetingIntegration.create_table(engine)
    logger.info("ZoomMeetingIntegration table creation complete.")

    # Insert sample meeting
    app_user_id = "sampleuser@example.com"  # Define app_user_id before use
    scheduled_start_time = datetime(2024, 6, 1, 14, 0, tzinfo=pytz.timezone("America/New_York"))  # Example start time
    new_meeting = ZoomMeetingIntegration.insert_table(
        meeting_id=79936192621,
        host_url="https://zoom.example.com/host",
        join_url="https://zoom.example.com/join",
        start_url="https://zoom.example.com/start",
        meeting_password="123456",
        meeting_topic="Project Kickoff",
        meeting_agenda="Discuss project objectives and deliverables",
        start_time=scheduled_start_time,      # ← was .isoformat(); keep it as datetime
        duration_minutes=90,
        timezone="America/New_York",
        status_id=1,
        integration_id=1,
        created_by=1,
        updated_by=1,
        app_user_id=app_user_id
    )

    logger.info(f"Inserted Meeting Details: {new_meeting}")
