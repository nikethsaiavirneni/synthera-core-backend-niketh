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
from typing import List, Optional

# ================================
# Third-party imports
# ================================
import pytz
from sqlalchemy import Column, Integer, BigInteger, String, Text, TIMESTAMP, ForeignKey, Boolean, UUID, ARRAY, inspect, text
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

# Create engine using the centralized connection utility and instantiate session management.
engine = get_engine()
db_util = DBSessionUtil(engine)



# ================================
# Model Definition - Meeting Attendees
# ================================
class MeetingAttendee(Base):
    """
    Meeting attendees model aligned with actual DB schema.
    """
    __tablename__ = 'meeting_attendee'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    meeting_id = Column(BigInteger, ForeignKey('meeting.meeting_id', ondelete='CASCADE'), nullable=False)
    employee_id = Column(BigInteger, ForeignKey('employees.emp_id', ondelete='CASCADE'), nullable=False)
    status = Column(String(20), default='pending')  # pending, accepted, declined, tentative
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
    
    @classmethod
    def insert_table(cls, session: Session, **kwargs):
        """Insert a new meeting attendee record (skip duplicates)."""
        logger.debug(f"Adding attendee to meeting with data: {kwargs}")

        # Prevent duplicate insert
        existing = session.query(cls).filter_by(
            meeting_id=kwargs.get("meeting_id"),
            employee_id=kwargs.get("employee_id")
        ).first()

        if existing:
            logger.info(f"Attendee {kwargs.get('employee_id')} already exists for meeting {kwargs.get('meeting_id')}, skipping insert.")
            return existing

        new_attendee = cls(**kwargs)
        session.add(new_attendee)
        session.commit()
        logger.info(f"Added attendee {kwargs.get('employee_id')} to meeting {kwargs.get('meeting_id')}")
        return new_attendee

    @classmethod
    def create_table(cls, engine):
        """Create the meeting_attendees table if it doesn't exist."""
        inspector = inspect(engine)
        if cls.__tablename__ not in inspector.get_table_names():
            cls.__table__.create(bind=engine)
            logger.info("Table 'meeting_attendees' created successfully.")
        else:
            logger.info("Table 'meeting_attendees' already exists. Skipping creation.")

    @classmethod
    def drop_table(cls, engine):
        """Drop the meeting_attendees table."""
        cls.__table__.drop(bind=engine, checkfirst=True)
        logger.info("Table 'meeting_attendees' dropped successfully.")

    
    @classmethod
    def update_table(cls, session: Session, meeting_id: int, emp_id: int, **kwargs):
        """Update an existing meeting attendee record."""
        logger.debug(f"Updating attendee {emp_id} for meeting {meeting_id} with data: {kwargs}")
        attendee = session.query(cls).filter_by(meeting_id=meeting_id, emp_id=emp_id).first()
        if attendee:
            for key, value in kwargs.items():
                setattr(attendee, key, value)
            attendee.updated_at = datetime.now(pytz.utc)
            session.commit()
            logger.info(f"Updated attendee {emp_id} for meeting {meeting_id}")
        else:
            logger.warning(f"Attendee {emp_id} for meeting {meeting_id} not found.")
        return attendee

    @classmethod
    def get_table(cls, session: Session, **filters):
        """Fetch meeting attendee records with optional filters."""
        logger.debug(f"Fetching meeting attendees with filters: {filters}")
        attendees = session.query(cls).filter_by(**filters).all()
        logger.info(f"Fetched {len(attendees)} meeting attendee(s) with filters: {filters}")
        return attendees

    @classmethod
    def get_meeting_attendees(cls, session: Session, meeting_id: int):
        """Get all attendees for a specific meeting."""
        logger.debug(f"Fetching attendees for meeting ID: {meeting_id}")
        attendees = session.query(cls).filter_by(meeting_id=meeting_id).all()
        logger.info(f"Found {len(attendees)} attendees for meeting {meeting_id}")
        return attendees

    @classmethod
    def get_user_meetings(cls, session: Session, emp_id: int):
        """Get all meetings for a specific employee."""
        logger.debug(f"Fetching meetings for employee ID: {emp_id}")
        attendees = session.query(cls).filter_by(emp_id=emp_id).all()
        logger.info(f"Found {len(attendees)} meetings for employee {emp_id}")
        return attendees

    @classmethod
    def bulk_insert_attendees(cls, session: Session, meeting_id: int, emp_ids: List[int], role: str = 'attendee'):
        """Bulk insert multiple attendees for a meeting."""
        logger.debug(f"Bulk inserting {len(emp_ids)} attendees for meeting {meeting_id}")
        attendees = []
        for emp_id in emp_ids:
            attendee = cls(meeting_id=meeting_id, emp_id=emp_id, role=role)
            attendees.append(attendee)
        
        session.add_all(attendees)
        session.commit()
        logger.info(f"Bulk inserted {len(attendees)} attendees for meeting {meeting_id}")
        return attendees

    def to_dict(self):
        """Convert meeting attendee instance to dictionary."""
        return {
            'meeting_id': self.meeting_id,
            'employee_id': self.employee_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    logger.info("Starting calendar models script execution")
    
    try:
        # Create tables
        MeetingAttendee.create_table(engine)
        logger.info("Calendar models table creation complete.")

        # Example usage (commented out for production)
        # with db_util.session_scope() as session:
        #     # Insert a sample holiday
        #     new_holiday = Holiday.insert_table(
        #         session,
        #         title="Company Foundation Day",
        #         description="Annual company anniversary celebration",
        #         region="US",
        #         start_at=datetime(2025, 6, 15, 0, 0, tzinfo=pytz.utc),
        #         end_at=datetime(2025, 6, 15, 23, 59, tzinfo=pytz.utc),
        #         all_day=True,
        #         holiday_type="company",
        #         rrule="FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=15"
        #     )
        #     logger.info("Sample holiday insertion complete.")

        logger.info("Calendar models script completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in calendar models script: {str(e)}")
        logger.exception("Full exception details:")
        raise
