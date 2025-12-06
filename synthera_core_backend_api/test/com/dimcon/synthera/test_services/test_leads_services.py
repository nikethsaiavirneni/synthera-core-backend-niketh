import pytest
from unittest.mock import patch, MagicMock

from com.dimcon.synthera.routes.req_routes import RequestRouter


@pytest.fixture
def mock_services():
    with patch("com.dimcon.synthera.routes.req_routes.LeadService") as mock_leads, \
         patch("com.dimcon.synthera.routes.req_routes.ChimeService") as mock_chime, \
         patch("com.dimcon.synthera.routes.req_routes.ResponseBuilder") as mock_response_builder:
        yield mock_leads, mock_chime, mock_response_builder


def test_get_all_leads_success(mock_services):
    mock_leads, _, mock_response = mock_services
    mock_leads.get_all_leads.return_value = [{"id": 1, "name": "Lead A"}]
    mock_response.build_response.return_value = {"statusCode": 200, "body": "wrapped"}

    result = RequestRouter.route_request("GET", "/leads", {}, {"queryStringParameters": {}})
    assert result == {"statusCode": 200, "body": "wrapped"}
    mock_leads.get_all_leads.assert_called_once()
    mock_response.build_response.assert_called_once()


def test_get_lead_by_id_success(mock_services):
    mock_leads, _, mock_response = mock_services
    mock_leads.get_lead_by_id.return_value = {"id": 1, "name": "Lead A"}
    mock_response.build_response.return_value = {"statusCode": 200, "body": "wrapped"}

    result = RequestRouter.route_request("GET", "/leads", {"id": "1"}, {})
    mock_leads.get_lead_by_id.assert_called_once_with("1")
    assert result == {"statusCode": 200, "body": "wrapped"}


def test_post_lead(mock_services):
    mock_leads, _, mock_response = mock_services
    mock_leads.create_lead.return_value = {"id": 10, "name": "New Lead"}
    mock_response.build_response.return_value = {"statusCode": 200, "body": "wrapped"}

    result = RequestRouter.route_request("POST", "/leads", {}, {"body": '{"name": "New Lead"}'})
    mock_leads.create_lead.assert_called_once()
    assert result == {"statusCode": 200, "body": "wrapped"}


def test_put_lead(mock_services):
    mock_leads, _, mock_response = mock_services
    mock_leads.update_lead.return_value = {"id": 5, "updated": True}
    mock_response.build_response.return_value = {"statusCode": 200, "body": "wrapped"}

    result = RequestRouter.route_request("PUT", "/leads", {"id": "5"}, {"body": '{"name": "Updated"}'})
    mock_leads.update_lead.assert_called_once_with(5, {"body": '{"name": "Updated"}'})
    assert result == {"statusCode": 200, "body": "wrapped"}


def test_delete_lead(mock_services):
    mock_leads, _, mock_response = mock_services
    mock_leads.delete_lead.return_value = {"id": 3, "deleted": True}
    mock_response.build_response.return_value = {"statusCode": 200, "body": "wrapped"}

    result = RequestRouter.route_request("DELETE", "/leads", {"id": "3"}, {})
    mock_leads.delete_lead.assert_called_once_with(3)
    assert result == {"statusCode": 200, "body": "wrapped"}


def test_invalid_resource(mock_services):
    _, _, mock_response = mock_services
    mock_response.build_response.return_value = {"statusCode": 404, "body": "not found"}

    result = RequestRouter.route_request("GET", "/unknown", {}, {})
    assert result["statusCode"] == 404
    mock_response.build_response.assert_called_once_with(404, {"error": "Resource not found"})


def test_invalid_http_method(mock_services):
    _, _, mock_response = mock_services
    mock_response.build_response.return_value = {"statusCode": 400, "body": "bad request"}

    result = RequestRouter.route_request("PATCH", "/leads", {}, {})
    assert result["statusCode"] == 400
    mock_response.build_response.assert_called_once_with(400, {"error": "Invalid request"})


def test_exception_handling(mock_services):
    mock_leads, _, mock_response = mock_services
    mock_leads.get_all_leads.side_effect = Exception("DB error")
    mock_response.build_response.return_value = {"statusCode": 500, "body": "internal error"}

    result = RequestRouter.route_request("GET", "/leads", {}, {"queryStringParameters": {}})
    assert result["statusCode"] == 500
    mock_response.build_response.assert_called_once_with(500, {"error": "Internal server error"})
