import pytest
import json

# ✅ Fixture to patch ResponseBuilder.build_response
@pytest.fixture
def patch_response_builder(monkeypatch):
    """Monkeypatches ResponseBuilder to return simplified mock responses."""
    def custom_response(status_code, body, headers=None):
        return {
            "statusCode": status_code,
            "body": json.dumps(body),
            "headers": headers or {
                "Content-Type": "application/json"
            }
        }

    monkeypatch.setattr(
        "com.dimcon.synthera.utilities.responses.ResponseBuilder.build_response",
        custom_response
    )



@pytest.fixture
def patch_route_request(mocker):
    return mocker.patch("com.dimcon.synthera.routes.req_routes.RequestRouter.route_request")



@pytest.fixture
def patch_logger(mocker):
    return mocker.patch("com.dimcon.synthera.utilities.log_handler.LoggerManager")

@pytest.fixture
def patch_session_scope(mocker):
    return mocker.patch("com.dimcon.synthera.utilities.sessions_manager.DBSessionUtil.session_scope")


