"""
Example of how CalendarService works with API Gateway Cognito Authorizer

This file demonstrates the event structure that API Gateway sends to your Lambda function
when using a Cognito User Pool Authorizer.
"""

# Example Lambda event from API Gateway with Cognito Authorizer
api_gateway_event_example = {
    "resource": "/calendar",
    "path": "/calendar",
    "httpMethod": "GET",
    "headers": {
        "Accept": "application/json",
        "Authorization": "Bearer eyJraWQiOiJwVWZ1MlJmWEVIXC9kZUdyNzY2bzRETVViTkNOa2Q3UUwzVDY0QjZnNHVWRT0iLCJhbGciOiJSUzI1NiJ9...",
        "Host": "ceon98kjte.execute-api.us-east-1.amazonaws.com",
        "User-Agent": "PostmanRuntime/7.44.0",
        "X-Forwarded-Proto": "https"
    },
    "multiValueHeaders": {
        "Accept": ["application/json"],
        "Authorization": ["Bearer eyJraWQiOiJwVWZ1..."]
    },
    "queryStringParameters": {
        "start": "2025-08-01",
        "tz": "America/New_York"
    },
    "multiValueQueryStringParameters": {
        "start": ["2025-08-01"],
        "tz": ["America/New_York"]
    },
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "abc123",
        "authorizer": {
            # This is the key part - API Gateway adds user claims here
            "claims": {
                "at_hash": "AgloDmjPsc279bYx0LWB_w",
                "sub": "34f84428-20b1-7052-98cf-8d3ac200c040",  # Cognito User ID
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_kQLWUoOi1",
                "cognito:username": "vksolleti",  # Username
                "aud": "5hdbhtbjh1uuu44b67g6dlm842",
                "event_id": "45aff011-171f-455c-bbb8-df3118cbaba7",
                "token_use": "id",
                "auth_time": "1748471941",
                "exp": "Wed May 28 23:39:01 UTC 2025",
                "iat": "Wed May 28 22:39:01 UTC 2025",
                "jti": "56c6be0e-2a4b-4896-be4f-0399213ee44e",
                "email": "vamsikrishna.solleti@dimcon.com"  # User email
            }
        },
        "resourcePath": "/calendar",
        "httpMethod": "GET",
        "path": "/dev/calendar",
        "accountId": "528757797189",
        "protocol": "HTTP/1.1",
        "stage": "dev",
        "requestId": "1ad51e07-dad0-47e2-a177-d8d7c1c5883d"
    },
    "body": None,
    "isBase64Encoded": False
}

# Example event for creating a calendar event (POST request)
create_event_example = {
    "resource": "/calendar/events",
    "path": "/calendar/events",
    "httpMethod": "POST",
    "headers": {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJraWQiOiJwVWZ1...",
        "Host": "ceon98kjte.execute-api.us-east-1.amazonaws.com"
    },
    "queryStringParameters": None,
    "pathParameters": None,
    "requestContext": {
        "authorizer": {
            "claims": {
                "sub": "34f84428-20b1-7052-98cf-8d3ac200c040",
                "cognito:username": "vksolleti",
                "email": "vamsikrishna.solleti@dimcon.com"
            }
        },
        "httpMethod": "POST",
        "path": "/dev/calendar/events"
    },
    "body": """{
        "kind": "MEETING",
        "title": "Team Standup",
        "description": "Daily team synchronization meeting",
        "startLocal": "2025-08-21T09:00:00",
        "endLocal": "2025-08-21T09:30:00",
        "tzid": "America/New_York",
        "allDay": false,
        "scope": "ORG",
        "attendees": ["emp_123", "emp_456"],
        "recurrence": {
            "freq": "WEEKLY",
            "byday": ["MO", "TU", "WE", "TH", "FR"],
            "ends": {
                "type": "COUNT",
                "count": 50
            }
        }
    }""",
    "isBase64Encoded": False
}

def demo_calendar_service():
    """
    Demo how CalendarService works with API Gateway events
    """
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    
    from com.dimcon.synthera.services.calendar_service import CalendarService
    
    print("🚀 CalendarService API Gateway Integration Demo")
    print("=" * 60)
    
    try:
        # Initialize the service
        service = CalendarService()
        print("✅ CalendarService initialized successfully")
        
        # Demo 1: Get month calendar
        print("\n📅 Demo 1: Get Month Calendar")
        print("-" * 40)
        print("Event structure received from API Gateway:")
        print(f"  - HTTP Method: {api_gateway_event_example['httpMethod']}")
        print(f"  - Resource: {api_gateway_event_example['resource']}")
        print(f"  - Query Params: {api_gateway_event_example['queryStringParameters']}")
        print(f"  - Cognito Sub: {api_gateway_event_example['requestContext']['authorizer']['claims']['sub']}")
        print(f"  - User Email: {api_gateway_event_example['requestContext']['authorizer']['claims']['email']}")
        
        # Uncomment to test (requires database connection):
        # result = service.get_month_calendar(api_gateway_event_example)
        # print(f"Calendar result: {result['statusCode']}")
        
        # Demo 2: Create event
        print("\n📝 Demo 2: Create Calendar Event")
        print("-" * 40)
        print("Event structure for creating meeting:")
        print(f"  - HTTP Method: {create_event_example['httpMethod']}")
        print(f"  - Resource: {create_event_example['resource']}")
        print(f"  - Has Body: {create_event_example['body'] is not None}")
        print(f"  - User: {create_event_example['requestContext']['authorizer']['claims']['cognito:username']}")
        
        # Uncomment to test (requires database connection):
        # result = service.create_event(create_event_example)
        # print(f"Create event result: {result['statusCode']}")
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 Key Benefits of API Gateway Authorizer:")
        print("  - JWT validation happens at API Gateway level")
        print("  - Invalid tokens never reach your Lambda")
        print("  - User claims are automatically extracted")
        print("  - No need for JWT libraries in your Lambda code")
        print("  - Better performance and security")
        
    except Exception as e:
        print(f"❌ Demo error: {str(e)}")
        import traceback
        traceback.print_exc()

def show_authentication_flow():
    """
    Show the complete authentication flow
    """
    print("\n🔐 Authentication Flow with API Gateway")
    print("=" * 60)
    
    steps = [
        "1. Client sends request with Authorization: Bearer <jwt_token>",
        "2. API Gateway validates JWT token against Cognito User Pool",
        "3. If valid, API Gateway extracts claims and adds to requestContext",
        "4. Lambda receives event with user claims in requestContext.authorizer.claims",
        "5. CalendarService._extract_user_context_from_event() reads claims",
        "6. Service looks up user in database using cognito_sub or email",
        "7. Service builds user_context with org_id, user_id, region, etc.",
        "8. Business logic proceeds with authenticated user context"
    ]
    
    for step in steps:
        print(f"  {step}")
    
    print("\n📋 Required Database Setup:")
    print("  - Add cognito_sub column to employees table (optional)")
    print("  - Ensure email column exists for fallback lookup") 
    print("  - Add region column for holiday/timezone support")
    
    print("\n⚙️ API Gateway Configuration:")
    print("  - Create Cognito User Pool Authorizer")
    print("  - Set Authorization header as identity source")
    print("  - Configure authorizer on calendar endpoints")

if __name__ == "__main__":
    show_authentication_flow()
    demo_calendar_service()
