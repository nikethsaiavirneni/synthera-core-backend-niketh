import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from datetime import datetime
import pytz
import logging
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, inspect, create_engine
from sqlalchemy.orm import sessionmaker
from com.dimcon.synthera.resources.base import Base
from com.dimcon.synthera.resources.organization_and_employees.employees import Employee
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

engine = get_engine()
db_util = DBSessionUtil(engine)

class Industry(Base):
    __tablename__ = 'industries'

    industry_id = Column(Integer, primary_key=True, autoincrement=True)
    industry_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey(Employee.emp_id), nullable=False)
    updated_by = Column(Integer, ForeignKey(Employee.emp_id))
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(pytz.utc), onupdate=datetime.now(pytz.utc))

    @classmethod
    def insert_table(cls, **kwargs):
        new_industry = cls(**kwargs)
        with db_util.session_scope() as session:
            session.add(new_industry)
            session.commit()
            logger.info(f"Inserted industry with ID: {new_industry.industry_id}")
        return new_industry

    @classmethod
    def get_table(cls, **filters):
        with db_util.session_scope() as session:
            industries = session.query(cls).filter_by(**filters).all()
            logger.info(f"Fetched {len(industries)} industry(ies) with filters: {filters}")
        return industries

def create_industries_table():
    """Create the industries table in the database if it does not exist."""
    engine = get_engine()
    Base.metadata.create_all(engine, tables=[Industry.__table__])
    logger.info("Industries table created (if not exists).")

if __name__ == "__main__":
    create_industries_table()