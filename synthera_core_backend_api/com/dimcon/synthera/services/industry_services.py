import json
from com.dimcon.synthera.resources.industries.industry import Industry
from com.dimcon.synthera.resources.organization_and_employees.employees import Employee
from com.dimcon.synthera.utilities.responses import ResponseBuilder
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

engine = get_engine()
db_util = DBSessionUtil(engine)

class IndustryService:
    @classmethod
    def get_all_industries(cls):
        try:
            with db_util.session_scope() as session:
                industries = session.query(Industry).all()
                result = [
                    {
                        "industry_id": i.industry_id,
                        "industry_name": i.industry_name,
                        "description": i.description,
                        "created_by": i.created_by,
                        "updated_by": i.updated_by,
                        "created_at": str(i.created_at),
                        "updated_at": str(i.updated_at)
                    }
                    for i in industries
                ]
            return ResponseBuilder.build_response(200, {"message": "Success", "data": result})
        except Exception as e:
            logger.error("Error fetching industries", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})

    @classmethod
    def create_industry(cls, event: dict):
        try:
            if "body" not in event:
                return ResponseBuilder.build_response(400, {"error": "Missing request body"})
            try:
                data = json.loads(event["body"])
            except Exception:
                return ResponseBuilder.build_response(400, {"error": "Invalid JSON format"})
            required_fields = ["industry_name", "description"]
            if not all(field in data for field in required_fields):
                return ResponseBuilder.build_response(400, {"error": "Missing required fields"})
            cognito_sub = event.get("requestContext", {}).get("authorizer", {}).get("claims", {}).get("sub")
            if not cognito_sub:
                return ResponseBuilder.build_response(401, {"error": "Unauthorized: Missing Cognito sub"})
            with db_util.session_scope() as session:
                employee = session.query(Employee).filter_by(cognito_sub=cognito_sub).first()
                if not employee:
                    return ResponseBuilder.build_response(401, {"error": "Employee not found"})
                emp_id = employee.emp_id
                new_industry = Industry(
                    industry_name=data["industry_name"],
                    description=data["description"],
                    created_by=emp_id,
                    updated_by=emp_id
                )
                session.add(new_industry)
                session.commit()
                # Extract attributes before session closes
                industry_dict = {
                    "industry_id": new_industry.industry_id,
                    "industry_name": new_industry.industry_name,
                    "description": new_industry.description,
                    "created_by": new_industry.created_by,
                    "updated_by": new_industry.updated_by,
                    "created_at": str(new_industry.created_at),
                    "updated_at": str(new_industry.updated_at)
                }
            return ResponseBuilder.build_response(200, {
                "message": "Success",
                "data": industry_dict
            })
        except Exception as e:
            logger.error("Error creating industry", exc_info=True)
            return ResponseBuilder.build_response(500, {"error": "Internal server error"})