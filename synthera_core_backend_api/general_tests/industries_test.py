import pytest
import json
from com.dimcon.synthera.services.leads_services import LeadService
from com.dimcon.synthera.services.industry_services import IndustryService

# Mock event helpers
def mock_event(body_dict, cognito_sub="test-sub-123"):
    return {
        "body": json.dumps(body_dict),
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": cognito_sub
                }
            }
        }
    }

# @pytest.mark.usefixtures("db_session")  # Remove or comment this line
class TestLeadStagesAndIndustries:

    def test_create_lead_stage(self):
        event = mock_event({
            "stage_name": "Test Stage",
            "description": "Test Description"
        })
        response = LeadService.create_lead_stage(event)
        assert response["statusCode"] == 200
        data = json.loads(response["body"])["data"]
        assert data["stage_name"] == "Test Stage"
        assert data["description"] == "Test Description"

    def test_get_lead_stages(self):
        response = LeadService.get_all_lead_stages()
        assert response["statusCode"] == 200
        data = json.loads(response["body"])["data"]
        assert isinstance(data, list)
        assert any(stage["stage_name"] == "Test Stage" for stage in data)

    def test_create_industry(self):
        event = mock_event({
            "industry_name": "Test Industry",
            "description": "Industry Description"
        })
        response = IndustryService.create_industry(event)
        assert response["statusCode"] == 200
        data = json.loads(response["body"])["data"]
        assert data["industry_name"] == "Test Industry"
        assert data["description"] == "Industry Description"

    def test_get_industries(self):
        response = IndustryService.get_all_industries()
        assert response["statusCode"] == 200
        data = json.loads(response["body"])["data"]
        assert isinstance(data, list)
        assert any(ind["industry_name"] == "Test Industry" for ind in data)