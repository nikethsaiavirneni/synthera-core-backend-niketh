import json
import pytest
from unittest.mock import MagicMock
from contextlib import contextmanager

# Import your ChimeService and model
import com.dimcon.synthera.services.chime_service as cs
from com.dimcon.synthera.resources.leads.leads_details import LeadDetail


# ✅ Mock AWS Chime client
@pytest.fixture
def mock_chime_client(monkeypatch):
    mock_client = MagicMock()
    mock_client.create_meeting.return_value = {
        "Meeting": {
            "MeetingId": "mock-meeting-id",
            "MediaPlacement": {
                "AudioHostUrl": "https://audio.url",
                "ScreenDataUrl": "https://screen.data",
                "ScreenSharingUrl": "https://screen.share",
                "ScreenViewingUrl": "https://screen.view",
                "SignalingUrl": "https://signaling.url",
                "TurnControlUrl": "https://turn.control"
            }
        }
    }
    mock_client.create_attendee.return_value = {
        "Attendee": {
            "AttendeeId": "mock-attendee-id",
            "JoinToken": "mock-token"
        }
    }
    monkeypatch.setattr(cs, "chime_client", mock_client)


# ✅ Mock DB session including .flush()
@pytest.fixture
def mock_db_session(monkeypatch):
    class DummySession:
        def query(self, model):
            class DummyQuery:
                def filter_by(self, **kwargs):
                    class Result:
                        def first(inner_self):
                            return LeadDetail(lead_id=kwargs.get("lead_id", 1))
                    return Result()
            return DummyQuery()
        def add(self, obj): pass
        def commit(self): pass
        def refresh(self, obj): obj.meeting_id = 999
        def flush(self): pass  # ✅ Required for DAO insert()
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    dummy_session = DummySession()

    @contextmanager
    def dummy_session_scope(self=None):
        yield dummy_session

    # ✅ Patch DBSessionUtil.session_scope in chime_service
    monkeypatch.setattr(cs.DBSessionUtil, "session_scope", dummy_session_scope)

    # ✅ Patch MeetingService.db_util.session_scope
    monkeypatch.setattr(cs.MeetingService, "db_util", MagicMock())
    cs.MeetingService.db_util.session_scope.return_value = dummy_session


# ✅ Patch SecretsManagerHandler to avoid config load error
@pytest.fixture(autouse=True)
def mock_secrets_manager(monkeypatch):
    mock_handler = MagicMock()
    monkeypatch.setattr(
        "com.dimcon.synthera.utilities.secrets_manager.SecretsManagerHandler",
        lambda config_file: mock_handler
    )


# ✅ Actual Test Case
def test_chime_meeting_creation(mock_chime_client, mock_db_session):
    event = {
        "body": json.dumps({
            "lead_id": 1,
            "scheduled_by": 1
        }),
        "headers": {
            "Accept-Language": "en-US"
        }
    }

    response = cs.ChimeService.create(event)

    assert isinstance(response, dict)
    assert "statusCode" in response
    assert response["statusCode"] in [200, 201]
