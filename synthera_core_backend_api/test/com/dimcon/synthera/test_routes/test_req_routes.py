import json
import pytest
from unittest.mock import MagicMock, patch
from com.dimcon.synthera.routes.req_routes import RequestRouter


class TestRequestRouter:

    def setup_method(self):
        # Patch ResponseBuilder for all tests
        self.build_response_patch = patch("com.dimcon.synthera.routes.req_routes.ResponseBuilder.build_response")
        self.mock_build_response = self.build_response_patch.start()
        self.mock_build_response.side_effect = lambda status, body: {
            "statusCode": status,
            "body": json.dumps(body)
        }

    def teardown_method(self):
        self.build_response_patch.stop()

    def test_valid_get_all_leads(self):
        mock_handler = MagicMock(return_value=[{"lead_first_name": "Test", "lead_last_name": "Lead"}])
        RequestRouter.entity_mapping["leads"]["get"] = mock_handler

        result = RequestRouter.route_request("GET", "/leads", {}, {"queryStringParameters": {}})
        body = json.loads(result["body"])

        assert result["statusCode"] == 200
        assert isinstance(body["data"], list)
        assert body["data"][0]["lead_first_name"] == "Test"

    def test_valid_get_lead_by_id(self):
        mock_handler = MagicMock(return_value={"lead_first_name": "Test", "lead_last_name": "Lead"})
        RequestRouter.entity_mapping["leads"]["get_by_id"] = mock_handler

        result = RequestRouter.route_request("GET", "/leads", {"id": "1"}, {})
        body = json.loads(result["body"])

        assert result["statusCode"] == 200
        assert body["data"]["lead_first_name"] == "Test"

    def test_valid_create_lead(self):
        mock_handler = MagicMock(return_value={"lead_first_name": "New", "lead_last_name": "Lead"})
        RequestRouter.entity_mapping["leads"]["post"] = mock_handler

        event = {"body": json.dumps({"lead_first_name": "New", "lead_last_name": "Lead"})}
        result = RequestRouter.route_request("POST", "/leads", {}, event)
        body = json.loads(result["body"])

        assert result["statusCode"] == 200
        assert body["data"]["lead_last_name"] == "Lead"

    def test_valid_update_lead(self):
        mock_handler = MagicMock(return_value={"lead_first_name": "Updated", "lead_last_name": "Lead"})
        RequestRouter.entity_mapping["leads"]["put"] = mock_handler

        event = {"body": json.dumps({"lead_first_name": "Updated", "lead_last_name": "Lead"})}
        result = RequestRouter.route_request("PUT", "/leads", {"id": "1"}, event)
        body = json.loads(result["body"])

        assert result["statusCode"] == 200
        assert body["data"]["lead_first_name"] == "Updated"

    def test_valid_delete_lead(self):
        mock_handler = MagicMock(return_value={"message": "Lead deleted"})
        RequestRouter.entity_mapping["leads"]["delete"] = mock_handler

        result = RequestRouter.route_request("DELETE", "/leads", {"id": "1"}, {})
        body = json.loads(result["body"])

        assert result["statusCode"] == 200
        assert body["data"]["message"] == "Lead deleted"

    def test_invalid_resource(self):
        result = RequestRouter.route_request("GET", "/invalid", {}, {})
        body = json.loads(result["body"])

        assert result["statusCode"] == 404
        assert body["error"] == "Resource not found"

    def test_invalid_method(self):
        result = RequestRouter.route_request("PATCH", "/leads", {}, {})
        body = json.loads(result["body"])

        assert result["statusCode"] == 400
        assert body["error"] == "Invalid request"

    def test_exception_handling(self):
        mock_handler = MagicMock(side_effect=Exception("Unexpected error"))
        RequestRouter.entity_mapping["leads"]["get"] = mock_handler

        result = RequestRouter.route_request("GET", "/leads", {}, {"queryStringParameters": {}})
        body = json.loads(result["body"])

        assert result["statusCode"] == 500
        assert body["error"] == "Internal server error"
