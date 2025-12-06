import json
import logging
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.resources.base_dao import BaseDAO
from com.dimcon.synthera.utilities.log_handler import LoggerManager
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility
from com.dimcon.synthera.resources.meeting.meeting import Meeting
from com.dimcon.synthera.resources.organization_and_employees.employees import Employee  # import your Employee model

logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

class MeetingService:
    engine = get_engine()
    dao = BaseDAO(engine)
    db_util = DBSessionUtil(engine)
    model_class = Meeting  # Set externally

    @classmethod
    def create(cls, event):
        try:
            logger.debug("Service: create called.")
            data = json.loads(event["body"])

            with cls.db_util.session_scope() as session:
                instance = cls.model_class(**data)
                cls.dao.insert(session, instance)
                session.commit()
                session.refresh(instance)
                return instance.to_dict()

        except Exception as e:
            logger.error("Service: Error during create", exc_info=True)
            raise

    @classmethod
    def get_by_id(cls, record_id):
        try:
            logger.debug(f"Service: get_by_id called with ID: {record_id}")
            with cls.db_util.session_scope() as session:
                record = cls.dao.fetch_by_id(session, cls.model_class, record_id)
                if not record:
                    raise ValueError(f"Record with id {record_id} not found")
                return record.to_dict()
        except Exception as e:
            logger.error("Service: Error during get_by_id", exc_info=True)
            raise
        

    @classmethod
    def get_all_meetings(cls, event, page=1, limit=10, sort_by="meeting_id", sort_order="asc", filters=None):
        try:
            logger.debug("Service: get_all_meetings called.")

            cognito_util = CognitoUserUtility()
            user_context = cognito_util.extract_user_context_from_event(event)
            cognito_sub = user_context.get("user_id") if user_context else None

            if cognito_sub is None:
                raise ValueError("User context not found or user_id missing.")

            with cls.db_util.session_scope() as session:
                # Lookup emp_id from Employee table using cognito_sub
                emp = session.query(Employee).filter(Employee.cognito_sub == cognito_sub).first()
                if not emp:
                    logger.debug(f"No employee found for cognito_sub: {cognito_sub}")
                    return []

                emp_id = emp.emp_id

                if filters is None:
                    filters = {}
                filters["created_by"] = emp_id

                logger.debug(f"Filters applied: {filters}, emp_id: {emp_id}")

                query = session.query(cls.model_class)
                for attr, value in filters.items():
                    if hasattr(cls.model_class, attr):
                        query = query.filter(getattr(cls.model_class, attr) == value)

                if hasattr(cls.model_class, sort_by):
                    sort_column = getattr(cls.model_class, sort_by)
                    if sort_order.lower() == "desc":
                        sort_column = sort_column.desc()
                    else:
                        sort_column = sort_column.asc()
                    query = query.order_by(sort_column)

                offset = (page - 1) * limit
                query = query.offset(offset).limit(limit)

                results = query.all()
                return [record.to_dict() for record in results]
        except Exception as e:
            logger.error("Service: Error during get_all", exc_info=True)
            raise

    @classmethod
    def update(cls, record_id, event):
        try:
            logger.debug(f"Service: update called for ID: {record_id}")
            update_data = json.loads(event["body"])
            with cls.db_util.session_scope() as session:
                updated = cls.dao.update(session, cls.model_class, record_id, update_data)
                session.commit()
                session.refresh(updated)
                return updated.to_dict()
        except Exception as e:
            logger.error("Service: Error during update", exc_info=True)
            raise

    @classmethod
    def delete(cls, record_id):
        try:
            logger.debug(f"Service: delete called for ID: {record_id}")
            with cls.db_util.session_scope() as session:
                cls.dao.delete(session, cls.model_class, record_id)
                session.commit()
                return {"message": "Record deleted successfully"}
        except Exception as e:
            logger.error("Service: Error during delete", exc_info=True)
            raise
