import os
import sys
import json
from datetime import datetime

# Add API root to sys.path for imports
api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if api_root not in sys.path:
    sys.path.insert(0, api_root)

from com.dimcon.synthera.services.meetings_service import MeetingService
from com.dimcon.synthera.resources.meeting.meeting import Meeting

def test_get_all_meetings():
    # Set the model_class for MeetingService
    MeetingService.model_class = Meeting

    # Prepare a sample event with a valid emp_id in the Cognito context
    # Replace '4' with an actual emp_id that exists in your DB for testing
    event = {
        "headers": {},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "email": "yogeswarsinghbondili@gmail.com",
                    "cognito:username": "yogeswarsinghbondili",
                    "sub": "04e8f468-0041-70e2-13f2-7cab7d18a9b5",
                    "token_use": "id"
                }
            }
        }
    }

    try:
        meetings = MeetingService.get_all(event)
        print(f"Total meetings found: {len(meetings)}")
        for meeting in meetings:
            print(json.dumps(meeting, indent=2, default=str))
    except Exception as e:
        print(f"Error querying meetings: {e}")

if __name__ == "__main__":
    test_get_all_meetings()