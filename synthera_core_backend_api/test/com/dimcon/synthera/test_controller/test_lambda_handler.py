import json
from com.dimcon.synthera.controller import lambda_entry_point

class TestLambdaHandler:
    def test_lambda_handler_missing_http_method(self, patch_response_builder):
        event = {
            "resource": "leads"
            # httpMethod is missing here
        }
            #assertion to check if the response is a 400 error
        result = lambda_entry_point.lambda_handler(event, None)
        assert result["statusCode"] == 400
        assert "Missing 'http_Method'" in result["body"]

    def test_lambda_handler_missing_resource(self, patch_response_builder):
        event = {
            "httpMethod": "GET"
            # resource is missing here
        }

        result = lambda_entry_point.lambda_handler(event, None)
        assert result["statusCode"] == 400
        assert "Missing 'resource'" in result["body"]

    def test_lambda_handler_valid_request(self, patch_route_request):
        event = {
            "httpMethod": "GET",
            "resource": "/leads"
        }

        result = lambda_entry_point.lambda_handler(event, None)
        assert result["statusCode"] == 200
        assert json.loads(result["body"]) == {"message": "Mocked route success"}
        