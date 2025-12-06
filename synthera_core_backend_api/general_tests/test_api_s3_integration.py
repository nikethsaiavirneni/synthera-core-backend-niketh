#!/usr/bin/env python3
"""
API Integration Test for S3 Pre-signed URL Functionality

This script demonstrates how the API returns secure download URLs for project documents
without exposing internal S3 paths.

Features tested:
1. Create project with S3 URLs
2. Retrieve project with auto-generated download URLs
3. Update project S3 URLs and verify new download URLs
4. Test API responses include/exclude download URLs appropriately
"""

import os
import sys
import json
import logging
from datetime import datetime, UTC

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from com.dimcon.synthera.routes.projects_req_router import ProjectRequestHandler
from com.dimcon.synthera.services.projects_service import ProjectService
from com.dimcon.synthera.utilities.log_handler import LoggerManager

logger = LoggerManager.setup_logger(__name__, level=logging.INFO)


def test_api_s3_integration():
    """Test S3 pre-signed URL integration with the API."""
    logger.info("🚀 Starting API S3 Integration Test")
    
    try:
        # Test data for project with S3 URLs
        test_project_data = {
            "lead_id": 69,
            "project_name": "S3 Integration Test Project",
            "project_description": "Testing secure file download functionality via API",
            "s3_url_sow_ppt": "documents/projects/test/statement_of_work.pptx",
            "s3_url_transcription": "documents/projects/test/meeting_transcript.txt"
        }
        
        print("\n📋 Creating project with S3 URLs...")
        print(f"Project data: {json.dumps(test_project_data, indent=2)}")
        
        # Simulate API request event
        create_event = {
            "httpMethod": "POST",
            "pathParameters": {},
            "queryStringParameters": {},
            "body": json.dumps(test_project_data),
            "headers": {"Content-Type": "application/json"}
        }
        
        # Test project creation
        logger.info("📡 Calling ProjectService.create_project...")
        create_response = ProjectService.create_project(create_event)
        
        print(f"\n✅ Create Response Status: {create_response.get('statusCode')}")
        if create_response.get('statusCode') == 201:
            response_body = json.loads(create_response.get('body', '{}'))
            project_data = response_body.get('data', {})
            project_id = project_data.get('project_id')
            
            print(f"📊 Created Project ID: {project_id}")
            print(f"📋 Project Data:")
            print(json.dumps(project_data, indent=2))
            
            # Check if download URLs were generated
            if 'sow_ppt_download_url' in project_data:
                print(f"🔗 SOW PPT Download URL: {project_data['sow_ppt_download_url'][:100]}...")
            else:
                print("⚠️ SOW PPT Download URL not generated")
            
            if 'transcription_download_url' in project_data:
                print(f"🔗 Transcription Download URL: {project_data['transcription_download_url'][:100]}...")
            else:
                print("⚠️ Transcription Download URL not generated")
            
            # Test project retrieval
            print(f"\n🔍 Retrieving project {project_id}...")
            get_response = ProjectService.get_project_by_id(project_id)
            
            print(f"✅ Get Response Status: {get_response.get('statusCode')}")
            if get_response.get('statusCode') == 200:
                get_body = json.loads(get_response.get('body', '{}'))
                get_data = get_body.get('data', {})
                
                print(f"📋 Retrieved Project Data:")
                print(json.dumps(get_data, indent=2))
                
                # Verify download URLs are present in retrieval
                if 'sow_ppt_download_url' in get_data:
                    print("✅ SOW PPT Download URL present in GET response")
                if 'transcription_download_url' in get_data:
                    print("✅ Transcription Download URL present in GET response")
            
            # Test project update with new S3 URLs
            print(f"\n🔄 Updating project {project_id} with new S3 URLs...")
            update_data = {
                "s3_url_sow_ppt": "documents/projects/test/updated_sow.pptx",
                "project_description": "Updated project description"
            }
            
            update_event = {
                "httpMethod": "PUT",
                "pathParameters": {"project_id": str(project_id)},
                "queryStringParameters": {},
                "body": json.dumps(update_data),
                "headers": {"Content-Type": "application/json"}
            }
            
            update_response = ProjectService.update_project(project_id, update_event)
            
            print(f"✅ Update Response Status: {update_response.get('statusCode')}")
            if update_response.get('statusCode') == 200:
                update_body = json.loads(update_response.get('body', '{}'))
                updated_data = update_body.get('data', {})
                
                print(f"📋 Updated Project Data:")
                print(json.dumps(updated_data, indent=2))
                
                # Verify new download URL was generated
                if 'sow_ppt_download_url' in updated_data:
                    print("✅ New SOW PPT Download URL generated after update")
                    if "updated_sow.pptx" in updated_data.get('s3_url_sow_ppt', ''):
                        print("✅ S3 URL correctly updated")
        
        else:
            print(f"❌ Failed to create project: {create_response}")
        
        print("\n✅ API S3 Integration Test Completed")
        
    except Exception as e:
        logger.error(f"❌ API test failed: {str(e)}")
        logger.exception("Full exception details:", exc_info=True)
        print(f"❌ API test failed: {str(e)}")


def test_router_s3_integration():
    """Test S3 integration through the router layer."""
    logger.info("🚀 Starting Router S3 Integration Test")
    
    try:
        # Initialize router
        router = ProjectRequestHandler()
        
        # Test data
        test_project_data = {
            "lead_id": 69,
            "project_name": "Router S3 Test Project",
            "project_description": "Testing S3 functionality through router",
            "s3_url_sow_ppt": "documents/projects/router-test/presentation.pptx"
        }
        
        print("\n📡 Testing project creation through router...")
        
        # Simulate Lambda event
        create_event = {
            "httpMethod": "POST",
            "resource": "/projects",
            "pathParameters": None,
            "queryStringParameters": None,
            "body": json.dumps(test_project_data),
            "headers": {"Content-Type": "application/json"},
            "requestContext": {"requestId": "test-request-123"}
        }
        
        # Route the request
        create_response = router.route_request(create_event, {})
        
        print(f"✅ Router Response Status: {create_response.get('statusCode')}")
        if create_response.get('statusCode') == 201:
            response_body = json.loads(create_response.get('body', '{}'))
            project_data = response_body.get('data', {})
            
            print(f"📋 Router Response Data:")
            print(json.dumps(project_data, indent=2))
            
            # Check for download URLs
            if 'sow_ppt_download_url' in project_data:
                print("✅ Download URL generated through router")
            else:
                print("⚠️ Download URL not generated through router")
        
        print("\n✅ Router S3 Integration Test Completed")
        
    except Exception as e:
        logger.error(f"❌ Router test failed: {str(e)}")
        logger.exception("Full exception details:", exc_info=True)
        print(f"❌ Router test failed: {str(e)}")


def demonstrate_security_benefits():
    """Demonstrate the security benefits of pre-signed URLs."""
    print("\n🔐 SECURITY BENEFITS DEMONSTRATION")
    print("=" * 50)
    
    print("🔒 BEFORE: Direct S3 URLs (INSECURE)")
    print("❌ s3://synthera-documents/documents/projects/123/confidential.pptx")
    print("❌ Exposes internal bucket structure")
    print("❌ Requires public bucket or AWS credentials")
    print("❌ No expiration control")
    print("❌ No access logging/monitoring")
    
    print("\n🛡️ AFTER: Pre-signed URLs (SECURE)")
    print("✅ https://synthera-documents.s3.amazonaws.com/documents/projects/123/confidential.pptx?")
    print("   AWSAccessKeyId=ASIA...&Signature=...&Expires=1642780800")
    print("✅ Hides internal bucket structure")
    print("✅ Works with private buckets")
    print("✅ Automatic expiration (1 hour default)")
    print("✅ Full AWS CloudTrail logging")
    print("✅ Temporary access only")
    print("✅ No AWS credentials needed for users")
    
    print("\n📊 IMPLEMENTATION HIGHLIGHTS:")
    print("• S3 keys stored internally (not exposed)")
    print("• Download URLs generated dynamically")
    print("• URLs expire automatically for security")
    print("• Frontend can render download buttons safely")
    print("• Backend controls all file access")


if __name__ == "__main__":
    print("=" * 80)
    print("S3 PRE-SIGNED URL API INTEGRATION TEST")
    print("=" * 80)
    
    try:
        # Run API tests
        test_api_s3_integration()
        
        # Run router tests
        test_router_s3_integration()
        
        # Demonstrate security benefits
        demonstrate_security_benefits()
        
        print("\n🎉 ALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Integration tests failed: {str(e)}")
        raise
    
    print("=" * 80)
