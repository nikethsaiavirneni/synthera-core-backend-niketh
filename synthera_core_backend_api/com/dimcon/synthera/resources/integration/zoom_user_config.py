# ================================
# Add project root to sys.path
# ================================
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
from datetime import datetime, UTC

# ================================
# Third-party imports
# ================================
from sqlalchemy import BigInteger, Column, Integer, String, TIMESTAMP, Text
from sqlalchemy.orm import Session

# ================================
# Centralized Logger and Database Utilities
# ================================
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility

# Create engine and session manager
engine = get_engine()
db_util = DBSessionUtil(engine)
cognito_util = CognitoUserUtility()

# ================================
# Project-specific imports
# ================================
from com.dimcon.synthera.resources.base import Base

# ================================
# Model Definition
# ================================
class ZoomUserConfig(Base):
    __tablename__ = 'zoom_user_config'
    __table_args__ = {'extend_existing': True}  # Add this line

    config_id = Column(Integer, primary_key=True, autoincrement=True)
    app_user_id = Column(String(255), nullable=False, unique=True)
    zoom_user_id = Column(String(255), nullable=True)
    
    # OAuth Token Fields
    access_token = Column(Text, nullable=True)  # Access token from Zoom
    refresh_token = Column(Text, nullable=True)  # Refresh token from Zoom
    token_type = Column(String(50), default='Bearer')
    expires_in = Column(Integer, nullable=True)  # Token expiry time in seconds
    scope = Column(Text, nullable=True)  # text in DB
    
    # User's Own Zoom App Configuration
    zoom_client_id = Column(String(255), nullable=True)  # User's Zoom app client ID
    zoom_client_secret = Column(Text, nullable=True)  # User's Zoom app client secret  
    zoom_redirect_uri = Column(String(500), nullable=True)  # User's Zoom app redirect URI
    created_by = Column(Integer, nullable=True)  # Employee ID who created this config
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(UTC))
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))

    @classmethod
    def create_table(cls, engine):
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if cls.__tablename__ not in inspector.get_table_names():
            cls.__table__.create(bind=engine)
            logger.info(f"Table '{cls.__tablename__}' created.")
        else:
            logger.info(f"Table '{cls.__tablename__}' already exists. Skipping creation.")

    @classmethod
    def drop_table(cls, engine):
        cls.__table__.drop(bind=engine, checkfirst=True)
        logger.info(f"Table '{cls.__tablename__}' dropped.")

    @classmethod
    def insert_table(cls, **kwargs):
        new_config = cls(**kwargs)
        with db_util.session_scope() as session:
            session.add(new_config)
            session.flush()
            logger.info(f"Inserted ZoomUserConfig with ID: {new_config.config_id}")
            config_dict = new_config.to_dict()
        return config_dict

    @classmethod
    def update_table(cls, config_id, **kwargs):
        with db_util.session_scope() as session:
            config = session.query(cls).filter_by(config_id=config_id).first()
            if config:
                for key, value in kwargs.items():
                    setattr(config, key, value)
                session.flush()
                logger.info(f"Updated ZoomUserConfig with ID: {config_id}")
                config_dict = config.to_dict()
            else:
                logger.warning(f"ZoomUserConfig with ID {config_id} not found.")
                config_dict = None
        return config_dict

    @classmethod
    def get_table(cls, **filters):
        with db_util.session_scope() as session:
            configs = session.query(cls).filter_by(**filters).all()
            configs_dict = [config.to_dict() for config in configs]
            logger.info(f"Fetched {len(configs)} ZoomUserConfig(s) with filters: {filters}")
        return configs_dict

    @classmethod
    def alter_table(cls):
        raise NotImplementedError("Use Alembic or raw SQL for altering tables.")

    def to_dict(self):
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
    ZoomUserConfig.create_table(engine)
    logger.info("ZoomUserConfig table creation complete.")

    # Insert sample config
    sample_config = ZoomUserConfig.insert_table(
        app_user_id="sampleuser@example.com",
        zoom_user_id="zoom-uid-123",
        access_token="sample-access-token",
        refresh_token="sample-refresh-token",
        token_type="Bearer",
        expires_in=3600,
        scope="meeting:read meeting:write",
        zoom_client_id="client-id-xyz",
        zoom_client_secret="client-secret-abc",
        zoom_redirect_uri="https://yourapp.com/zoom/callback",
        created_by=1
    )
    logger.info(f"Inserted ZoomUserConfig: {sample_config}")

    # Fetch and print all configs
    all_configs = ZoomUserConfig.get_table()
    logger.info(f"All ZoomUserConfigs: {all_configs}")

