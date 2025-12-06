# zoom_lambda_integration_test.py
"""
Integration test for Zoom Lambda flow (no mocks).
Calls lambda_handler for each Zoom route and prints the real response.
"""
import json
from com.dimcon.synthera.controller.lambda_entry_point import lambda_handler

# ---- CONFIGURE THESE VALUES FOR YOUR TEST ENVIRONMENT ----
TEST_USER_ID = "avirneninikethsai1144@gmail.com"  
TEST_CLIENT_ID = "MMxwciBScSEQG4rmkQ0w"
TEST_CLIENT_SECRET = "U1Cmk4SfdQyELufrfcm6eQUNN6lxseqR"
TEST_REDIRECT_URI = "https://xaw88y541i.execute-api.us-east-1.amazonaws.com/dev/zoom/callback"

# 1. /zoom/setup (POST)
print("\n--- /zoom/setup ---")
setup_event = {
    "httpMethod": "POST",
    "resource": "/zoom/setup",
    "body": json.dumps({
        "app_user_id": TEST_USER_ID,
        "zoom_client_id": TEST_CLIENT_ID,
        "zoom_client_secret": TEST_CLIENT_SECRET,
        "zoom_redirect_uri": TEST_REDIRECT_URI
    }),
    "headers": {},
    "queryStringParameters": {},
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "64480428-20b1-70af-312e-41882ba5183c",  # your employee's cognito_sub
                "email": "avirneninikethsai1144@gmail.com",
                "token_use": "id",  # <-- THIS MUST BE "id"
                "cognito:username": "avirneninikethsai1144@gmail.com"
            }
        }
    },
    "pathParameters": {},
}
setup_response = lambda_handler(setup_event, None)
print("Response:", setup_response)


# # 2. /zoom/meeting/create (POST)
# print("\n--- /zoom/meeting/create ---")
# create_event = {
#     "httpMethod": "POST",
#     "resource": "/zoom/create",
#     "body": json.dumps({
#         "topic": "Test Meeting",
#         "scheduled_start_time": "2025-09-27T05:00:00Z",
#         "lead_id": 68,  # Replace with a real lead_id
#         "lead_full_name": "yogi bondili",
#         "project_id": 10,  # Replace with a real project_id
#         "project_name": "1111",
#     }),
#     "headers": {},
#     "queryStringParameters": {},
#     "requestContext": {
#         "authorizer": {
#             "claims": {
#                 "sub": "64480428-20b1-70af-312e-41882ba5183c",
#                 "email": "avirneninikethsai1144@gmail.com",
#                 "token_use": "id",
#                 "cognito:username": "avirneninikethsai1144@gmail.com"
#             }
#         }
#     },
#     "pathParameters": {},
# }
# create_response = lambda_handler(create_event, None)
# print("Response:", create_response)

# 3. /zoom/meeting/update (PATCH)
# print("\n--- /zoom/meeting/update ---")
# update_event = {
#     "httpMethod": "PATCH",
#     "resource": "/zoom/update",
#     "body": json.dumps({
#         "meeting_id": 71943854064,  
#         "topic": "Updated Test Meeting",
#         "start_time": "2025-09-25T14:00:00Z"  # <-- Add or update this line
#     }),
#     "headers": {},
#     "queryStringParameters": {},
#     "requestContext": {
#         "authorizer": {
#             "claims": {
#                 "sub": "64480428-20b1-70af-312e-41882ba5183c",
#                 "email": "avirneninikethsai1144@gmail.com",
#                 "token_use": "id",
#                 "cognito:username": "avirneninikethsai1144@gmail.com"
#             }
#         }
#     },
#     "pathParameters": {},
# }
# update_response = lambda_handler(update_event, None)
# print("Response:", update_response)


# # 4. /zoom/delete (DELETE)
# print("\n--- /zoom/delete ---")
# delete_event = {
#     "httpMethod": "DELETE",
#     "resource": "/zoom/delete",
#     "body": json.dumps({
#         "meeting_id": 76774441579  # Replace with a real meeting_id
#     }),
#     "headers": {},
#     "queryStringParameters": {},
#     "requestContext": {
#         "authorizer": {
#             "claims": {
#                 "sub": "64480428-20b1-70af-312e-41882ba5183c",
#                 "email": "avirneninikethsai1144@gmail.com",
#                 "token_use": "id",
#                 "cognito:username": "avirneninikethsai1144@gmail.com"
#             }
#         }
#     },
#     "pathParameters": {},
# }
# delete_response = lambda_handler(delete_event, None)
# print("Response:", delete_response)

# print("\n--- Zoom Lambda integration test completed. ---")
