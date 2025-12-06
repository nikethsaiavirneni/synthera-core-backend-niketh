# zoom_lambda_delete_test.py
"""
Integration test for Zoom Lambda DELETE route only.
Calls lambda_handler for /zoom/delete and prints the real response.
"""
import json
from com.dimcon.synthera.controller.lambda_entry_point import lambda_handler

print("\n--- /zoom/delete ---")
delete_event = {
    "httpMethod": "DELETE",
    "resource": "/zoom/delete",
    "body": json.dumps({
        "meeting_id": 74605552272  # Replace with a real meeting_id
    }),
    "headers": {},
    "queryStringParameters": {},
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "64480428-20b1-70af-312e-41882ba5183c",
                "email": "avirneninikethsai1144@gmail.com",
                "token_use": "id",
                "cognito:username": "avirneninikethsai1144@gmail.com"
            }
        }
    },
    "pathParameters": {},
}
delete_response = lambda_handler(delete_event, None)
print("Response:", delete_response)
