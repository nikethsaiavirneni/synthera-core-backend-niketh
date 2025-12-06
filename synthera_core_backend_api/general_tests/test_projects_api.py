#!/usr/bin/env python3
"""
Test script for the Projects API implementation.
This script tests all CRUD operations for the project_leads table.
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from com.dimcon.synthera.controller.lambda_entry_point import lambda_handler

def test_projects_api():
    """Test all Projects API endpoints"""
    
    print("🚀 Testing Projects API Implementation...")
    print("=" * 50)
    
    # Test data
    test_project = {
        "lead_id": 69,  # Using niketh sai's lead_id
        "project_name": "API Test Project - niketh sai",
        "project_description": "A test project for API validation with comprehensive features including AI integration and workflow automation.",
        "s3_url_transcription": "s3://test-bucket/transcription.txt",
        "s3_url_sow_ppt": "s3://test-bucket/sow.pptx"
    }
    
    # 1. Test CREATE Project (POST)
    print("\n1️⃣ Testing CREATE Project (POST /projects)")
    create_event = {
        "httpMethod": "POST",
        "resource": "/projects",
        "pathParameters": None,
        "body": json.dumps(test_project),
        "queryStringParameters": None
    }
    
    try:
        response = lambda_handler(create_event, {})
        print(f"Status Code: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        
        if response['statusCode'] == 201:
            # Extract project_id for further tests
            response_data = json.loads(response['body'])
            created_project = response_data['data']
            project_id = created_project['project_id']
            print(f"✅ Project created successfully with ID: {project_id}")
        else:
            print("❌ Failed to create project")
            return
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return
    
    # 2. Test GET Project by ID (GET /projects/{id})
    print(f"\n2️⃣ Testing GET Project by ID (GET /projects/{project_id})")
    get_by_id_event = {
        "httpMethod": "GET",
        "resource": "/projects/{id}",
        "pathParameters": {"id": str(project_id)},
        "body": None,
        "queryStringParameters": None
    }
    
    try:
        response = lambda_handler(get_by_id_event, {})
        print(f"Status Code: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        
        if response['statusCode'] == 200:
            print("✅ Project retrieved successfully")
        else:
            print("❌ Failed to retrieve project")
    except Exception as e:
        print(f"❌ Error retrieving project: {e}")
    
    # 3. Test GET All Projects (GET /projects)
    print("\n3️⃣ Testing GET All Projects (GET /projects)")
    get_all_event = {
        "httpMethod": "GET",
        "resource": "/projects",
        "pathParameters": None,
        "body": None,
        "queryStringParameters": {"page": "1", "limit": "10", "sortBy": "project_name"}
    }
    
    try:
        response = lambda_handler(get_all_event, {})
        print(f"Status Code: {response['statusCode']}")
        response_data = json.loads(response['body'])
        print(f"Total projects: {response_data.get('total_count', 'N/A')}")
        print(f"Projects in response: {len(response_data.get('data', []))}")
        
        if response['statusCode'] == 200:
            print("✅ All projects retrieved successfully")
        else:
            print("❌ Failed to retrieve all projects")
    except Exception as e:
        print(f"❌ Error retrieving all projects: {e}")
    
    # 4. Test GET Projects by Lead ID (GET /projects?lead_id=69)
    print("\n4️⃣ Testing GET Projects by Lead ID (GET /projects?lead_id=69)")
    get_by_lead_event = {
        "httpMethod": "GET",
        "resource": "/projects",
        "pathParameters": None,
        "body": None,
        "queryStringParameters": {"lead_id": "69"}
    }
    
    try:
        response = lambda_handler(get_by_lead_event, {})
        print(f"Status Code: {response['statusCode']}")
        response_data = json.loads(response['body'])
        print(f"Projects for lead_id 69: {len(response_data.get('data', []))}")
        
        if response['statusCode'] == 200:
            print("✅ Projects by lead ID retrieved successfully")
        else:
            print("❌ Failed to retrieve projects by lead ID")
    except Exception as e:
        print(f"❌ Error retrieving projects by lead ID: {e}")
    
    # 5. Test UPDATE Project (PUT /projects/{id})
    print(f"\n5️⃣ Testing UPDATE Project (PUT /projects/{project_id})")
    update_data = {
        "project_name": "Updated API Test Project - niketh sai",
        "project_description": "Updated description with enhanced AI capabilities and improved workflow automation features.",
        "s3_url_transcription": "s3://updated-bucket/new-transcription.txt"
    }
    
    update_event = {
        "httpMethod": "PUT",
        "resource": "/projects/{id}",
        "pathParameters": {"id": str(project_id)},
        "body": json.dumps(update_data),
        "queryStringParameters": None
    }
    
    try:
        response = lambda_handler(update_event, {})
        print(f"Status Code: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        
        if response['statusCode'] == 200:
            print("✅ Project updated successfully")
        else:
            print("❌ Failed to update project")
    except Exception as e:
        print(f"❌ Error updating project: {e}")
    
    # 6. Test DELETE Project (DELETE /projects/{id})
    print(f"\n6️⃣ Testing DELETE Project (DELETE /projects/{project_id})")
    delete_event = {
        "httpMethod": "DELETE",
        "resource": "/projects/{id}",
        "pathParameters": {"id": str(project_id)},
        "body": None,
        "queryStringParameters": None
    }
    
    try:
        response = lambda_handler(delete_event, {})
        print(f"Status Code: {response['statusCode']}")
        print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
        
        if response['statusCode'] == 200:
            print("✅ Project deleted successfully")
        else:
            print("❌ Failed to delete project")
    except Exception as e:
        print(f"❌ Error deleting project: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Projects API testing completed!")

if __name__ == "__main__":
    test_projects_api()
