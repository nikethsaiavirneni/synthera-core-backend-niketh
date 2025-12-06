# ================================
# Add project root to sys.path
# ================================
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
from datetime import datetime

# ================================
# Third-party imports
# ================================
import pytz
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, inspect
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# ================================
# Project-specific imports
# ================================
import logging
from com.dimcon.synthera.utilities.log_handler import LoggerManager
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.resources.base import Base
from com.dimcon.synthera.resources.meeting.meeting_types import MeetingType
from com.dimcon.synthera.resources.meeting.meeting_priority import MeetingPriority
from com.dimcon.synthera.resources.leads.leads_details import LeadDetail
from com.dimcon.synthera.resources.organization_and_employees.employees import Employee

# ================================
# Model Definition
# ================================
class Meeting(Base):
    __tablename__ = 'meeting'

    meeting_id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_title = Column(String(255), nullable=False)
    meeting_description = Column(Text)
    meeting_type_id = Column(Integer, ForeignKey(MeetingType.meeting_type_id))
    meeting_priority_id = Column(Integer, ForeignKey(MeetingPriority.meeting_priority_id))
    lead_id = Column(Integer, ForeignKey(LeadDetail.lead_id))
    # store lead's full name as plain string (no FK to a non-PK column)
    lead_full_name = Column(String(255))
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=False)
    meeting_link = Column(String(500))
    
    # ================================
    # Calendar functionality additions
    # ================================
    org_id = Column(PG_UUID(as_uuid=True), nullable=True)  # Organization ID for calendar
    timezone = Column(String(100), default='UTC')  # Meeting timezone
    recurrence_rule = Column(Text, nullable=True)  # RRULE for recurring meetings
    end_time = Column(TIMESTAMP(timezone=True), nullable=True)  # Meeting end time
    # Add fields present in DB DDL
    scheduled_start_time = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.now(pytz.utc))
    scheduled_end_time = Column(TIMESTAMP(timezone=True), nullable=True, default=datetime.now(pytz.utc))
    meeting_status = Column(String(50), nullable=False, default='scheduled')
    meeting_priority_name = Column(String(255), nullable=True)
    meeting_type_name = Column(String(255), nullable=True)
    project_id = Column(Integer, nullable=True)
    project_name = Column(String(255), nullable=True)
    
    created_by = Column(Integer, ForeignKey(Employee.emp_id))
    updated_by = Column(Integer, ForeignKey(Employee.emp_id))
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc), onupdate=datetime.now(pytz.utc))

    @classmethod
    def create_table(cls, engine):
        inspector = inspect(engine)
        if cls.__tablename__ not in inspector.get_table_names():
            cls.__table__.create(bind=engine)
            logger.info("Table 'meeting' created.")
        else:
            logger.info("Table 'meeting' already exists. Skipping creation.")

    @classmethod
    def drop_table(cls, engine):
        cls.__table__.drop(bind=engine, checkfirst=True)
        logger.info("Table 'meeting' dropped.")

    @classmethod
    def insert_table(cls, session: Session, **kwargs):
        new_meeting = cls(**kwargs)
        session.add(new_meeting)
        session.commit()
        logger.info(f"Inserted meeting with ID: {new_meeting.meeting_id}")
        return new_meeting

    @classmethod
    def update_table(cls, session: Session, meeting_id: int, **kwargs):
        meeting = session.query(cls).filter_by(meeting_id=meeting_id).first()
        if meeting:
            for key, value in kwargs.items():
                setattr(meeting, key, value)
            session.commit()
            logger.info(f"Updated meeting with ID: {meeting_id}")
        else:
            logger.warning(f"Meeting with ID {meeting_id} not found.")
        return meeting

    @classmethod
    def get_table(cls, session: Session, **filters):
        meetings = session.query(cls).filter_by(**filters).all()
        logger.info(f"Fetched {len(meetings)} meeting(s) with filters: {filters}")
        return meetings

    @classmethod
    def alter_table(cls):
        raise NotImplementedError("Use Alembic or raw SQL for altering tables.")

# ================================
# Main Script Execution
# ================================