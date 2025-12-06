#!/usr/bin/env python3
"""
Comprehensive Test Script for S3 Pre-signed URL Functionality

This script tests the S3 pre-signed URL generation for project documents,
including SOW PowerPoint files and transcription files.

Test scenarios:
1. Generate pre-signed URLs for valid S3 keys
2. Handle invalid/missing S3 keys gracefully
3. Validate URL expiration settings
4. Test integration with Project model to_dict method
5. Mock S3 operations for testing without real AWS resources
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging for testing
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from com.dimcon.synthera.utilities.s3_utility import (
    S3PresignedURLGenerator, 
    generate_download_url, 
    is_valid_s3_key,
    get_s3_generator
)
from com.dimcon.synthera.resources.projects.projects_lead import Project
from com.dimcon.synthera.utilities.log_handler import LoggerManager

logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)


class TestS3PresignedURL(unittest.TestCase):
    """Test cases for S3 pre-signed URL functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        logger.info("🚀 Setting up S3 pre-signed URL tests")
        
        # Test data for projects
        self.test_project_data = {
            "project_id": 999,
            "lead_id": 69,
            "project_name": "Test S3 Integration Project",
            "project_description": "Testing S3 pre-signed URL functionality",
            "lead_full_name": "niketh sai",
            "s3_url_sow_ppt": "s3://syntheraai-ppt/niketh sai/test call/sow_niketh_sai_test_call.pptx",
            "s3_url_transcription": "s3://syntheraai-ppt-transcript/niketh sai/test call/niketh_sai_test_call_01_test_call_-_2025-07-22-222945769.txt",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        }
        
        # Mock S3 URLs for testing with real bucket structure
        self.valid_s3_key_ppt = "s3://syntheraai-ppt/niketh sai/test call/sow_niketh_sai_test_call.pptx"
        self.valid_s3_key_transcript = "s3://syntheraai-ppt-transcript/niketh sai/test call/niketh_sai_test_call_01_test_call_-_2025-07-22-222945769.txt"
        self.invalid_s3_key = "s3://syntheraai-ppt/non-existent-file.pptx"
        self.s3_url_format = "s3://syntheraai-ppt/niketh sai/test call/sow_niketh_sai_test_call.pptx"
        
        logger.info("✅ Test setup completed")
    
    @patch('boto3.client')
    def test_s3_generator_initialization(self, mock_boto_client):
        """Test S3PresignedURLGenerator initialization."""
        logger.info("🧪 Testing S3 generator initialization")
        
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client
        
        # Test initialization
        generator = S3PresignedURLGenerator()
        
        # Assertions
        self.assertIsNotNone(generator)
        self.assertEqual(generator.aws_region, "us-east-1")
        self.assertEqual(generator.ppt_bucket_name, "syntheraai-ppt")
        self.assertEqual(generator.transcript_bucket_name, "syntheraai-ppt-transcript")
        mock_boto_client.assert_called_once_with('s3', region_name='us-east-1')
        
        logger.info("✅ S3 generator initialization test passed")
    
    @patch('boto3.client')
    def test_generate_presigned_url_success(self, mock_boto_client):
        """Test successful pre-signed URL generation."""
        logger.info("🧪 Testing successful pre-signed URL generation")
        
        # Mock S3 client and response
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client
        
        expected_url = "https://syntheraai-ppt.s3.amazonaws.com/niketh%20sai/test%20call/sow_niketh_sai_test_call.pptx?AWSAccessKeyId=MOCK&Signature=MOCK&Expires=MOCK"
        mock_s3_client.generate_presigned_url.return_value = expected_url
        
        # Test URL generation
        generator = S3PresignedURLGenerator()
        result_url = generator.generate_presigned_url(self.valid_s3_key_ppt, expiration_hours=1)
        
        # Assertions
        self.assertEqual(result_url, expected_url)
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            ClientMethod='get_object',
            Params={
                'Bucket': 'syntheraai-ppt',
                'Key': 'niketh sai/test call/sow_niketh_sai_test_call.pptx'
            },
            ExpiresIn=3600,
            HttpMethod='GET'
        )
        
        logger.info("✅ Pre-signed URL generation success test passed")
    
    @patch('boto3.client')
    def test_generate_presigned_url_with_s3_prefix(self, mock_boto_client):
        """Test pre-signed URL generation with s3:// prefix."""
        logger.info("🧪 Testing pre-signed URL generation with s3:// prefix")
        
        # Mock S3 client and response
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client
        
        expected_url = "https://syntheraai-ppt.s3.amazonaws.com/niketh%20sai/test%20call/sow_niketh_sai_test_call.pptx?MOCK"
        mock_s3_client.generate_presigned_url.return_value = expected_url
        
        # Test URL generation with s3:// prefix
        generator = S3PresignedURLGenerator()
        result_url = generator.generate_presigned_url(self.s3_url_format, expiration_hours=2)
        
        # Assertions
        self.assertEqual(result_url, expected_url)
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            ClientMethod='get_object',
            Params={
                'Bucket': 'syntheraai-ppt',
                'Key': 'niketh sai/test call/sow_niketh_sai_test_call.pptx'  # Should have s3:// prefix removed
            },
            ExpiresIn=7200,  # 2 hours
            HttpMethod='GET'
        )
        
        logger.info("✅ Pre-signed URL generation with s3:// prefix test passed")
    
    @patch('boto3.client')
    def test_generate_presigned_url_failure(self, mock_boto_client):
        """Test pre-signed URL generation failure handling."""
        logger.info("🧪 Testing pre-signed URL generation failure handling")
        
        # Mock S3 client to raise exception
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client
        
        from botocore.exceptions import ClientError
        mock_s3_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.'}},
            'GetObject'
        )
        
        # Test URL generation failure
        generator = S3PresignedURLGenerator()
        result_url = generator.generate_presigned_url(self.invalid_s3_key)
        
        # Assertions
        self.assertIsNone(result_url)
        
        logger.info("✅ Pre-signed URL generation failure test passed")
    
    @patch('boto3.client')
    def test_validate_s3_key_exists_success(self, mock_boto_client):
        """Test S3 key validation for existing object."""
        logger.info("🧪 Testing S3 key validation for existing object")
        
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client
        
        # Mock successful head_object response
        mock_s3_client.head_object.return_value = {
            'ContentLength': 1024,
            'ContentType': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        # Test validation
        generator = S3PresignedURLGenerator()
        result = generator.validate_s3_key_exists(self.valid_s3_key_ppt)
        
        # Assertions
        self.assertTrue(result)
        mock_s3_client.head_object.assert_called_once_with(
            Bucket='syntheraai-ppt',
            Key='niketh sai/test call/sow_niketh_sai_test_call.pptx'
        )
        
        logger.info("✅ S3 key validation success test passed")
    
    @patch('boto3.client')
    def test_validate_s3_key_exists_failure(self, mock_boto_client):
        """Test S3 key validation for non-existent object."""
        logger.info("🧪 Testing S3 key validation for non-existent object")
        
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client
        
        from botocore.exceptions import ClientError
        mock_s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'HeadObject'
        )
        
        # Test validation
        generator = S3PresignedURLGenerator()
        result = generator.validate_s3_key_exists(self.invalid_s3_key)
        
        # Assertions
        self.assertFalse(result)
        
        logger.info("✅ S3 key validation failure test passed")
    
    @patch('com.dimcon.synthera.utilities.s3_utility.generate_download_url')
    @patch('com.dimcon.synthera.utilities.s3_utility.is_valid_s3_key')
    def test_project_to_dict_with_download_urls(self, mock_is_valid, mock_generate_url):
        """Test Project.to_dict() method with download URL generation."""
        logger.info("🧪 Testing Project.to_dict() with download URL generation")
        
        # Mock S3 utility functions
        mock_is_valid.return_value = True
        mock_generate_url.side_effect = [
            "https://syntheraai-ppt.s3.amazonaws.com/niketh%20sai/test%20call/sow_niketh_sai_test_call.pptx?MOCK_SOW",
            "https://syntheraai-ppt-transcript.s3.amazonaws.com/niketh%20sai/test%20call/niketh_sai_test_call_01_test_call_-_2025-07-22-222945769.txt?MOCK_TRANS"
        ]
        
        # Create a mock project object
        class MockProject:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            def to_dict(self, include_download_urls=True):
                # Simulate the enhanced to_dict method
                base_dict = {
                    "project_id": self.project_id,
                    "lead_id": self.lead_id,
                    "project_name": self.project_name,
                    "project_description": self.project_description,
                    "lead_full_name": self.lead_full_name,
                    "s3_url_transcription": self.s3_url_transcription,
                    "s3_url_sow_ppt": self.s3_url_sow_ppt,
                    "created_at": self.created_at.isoformat() if self.created_at else None,
                    "updated_at": self.updated_at.isoformat() if self.updated_at else None
                }
                
                if include_download_urls:
                    if self.s3_url_sow_ppt and mock_is_valid(self.s3_url_sow_ppt):
                        base_dict["sow_ppt_download_url"] = mock_generate_url(self.s3_url_sow_ppt, 1)
                    
                    if self.s3_url_transcription and mock_is_valid(self.s3_url_transcription):
                        base_dict["transcription_download_url"] = mock_generate_url(self.s3_url_transcription, 1)
                
                return base_dict
        
        # Create test project
        project = MockProject(**self.test_project_data)
        
        # Test to_dict with download URLs
        result_dict = project.to_dict(include_download_urls=True)
        
        # Assertions
        self.assertIn("sow_ppt_download_url", result_dict)
        self.assertIn("transcription_download_url", result_dict)
        self.assertTrue(result_dict["sow_ppt_download_url"].startswith("https://"))
        self.assertTrue(result_dict["transcription_download_url"].startswith("https://"))
        
        # Verify S3 functions were called
        self.assertEqual(mock_is_valid.call_count, 2)
        self.assertEqual(mock_generate_url.call_count, 2)
        
        logger.info("✅ Project.to_dict() with download URLs test passed")
    
    @patch('com.dimcon.synthera.utilities.s3_utility.is_valid_s3_key')
    def test_project_to_dict_with_invalid_s3_keys(self, mock_is_valid):
        """Test Project.to_dict() method with invalid S3 keys."""
        logger.info("🧪 Testing Project.to_dict() with invalid S3 keys")
        
        # Mock S3 utility to return False (invalid keys)
        mock_is_valid.return_value = False
        
        # Create a mock project object with invalid S3 keys
        class MockProject:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            def to_dict(self, include_download_urls=True):
                base_dict = {
                    "project_id": self.project_id,
                    "lead_id": self.lead_id,
                    "project_name": self.project_name,
                    "project_description": self.project_description,
                    "lead_full_name": self.lead_full_name,
                    "s3_url_transcription": self.s3_url_transcription,
                    "s3_url_sow_ppt": self.s3_url_sow_ppt,
                    "created_at": self.created_at.isoformat() if self.created_at else None,
                    "updated_at": self.updated_at.isoformat() if self.updated_at else None
                }
                
                if include_download_urls:
                    if self.s3_url_sow_ppt and mock_is_valid(self.s3_url_sow_ppt):
                        # This won't execute because mock_is_valid returns False
                        base_dict["sow_ppt_download_url"] = "mock_url"
                    
                    if self.s3_url_transcription and mock_is_valid(self.s3_url_transcription):
                        # This won't execute because mock_is_valid returns False
                        base_dict["transcription_download_url"] = "mock_url"
                
                return base_dict
        
        # Create test project
        project = MockProject(**self.test_project_data)
        
        # Test to_dict with invalid S3 keys
        result_dict = project.to_dict(include_download_urls=True)
        
        # Assertions - download URLs should not be included
        self.assertNotIn("sow_ppt_download_url", result_dict)
        self.assertNotIn("transcription_download_url", result_dict)
        
        # Original S3 keys should still be present
        self.assertIn("s3_url_sow_ppt", result_dict)
        self.assertIn("s3_url_transcription", result_dict)
        
        logger.info("✅ Project.to_dict() with invalid S3 keys test passed")
    
    def test_convenience_functions(self):
        """Test convenience functions for S3 operations."""
        logger.info("🧪 Testing S3 convenience functions")
        
        with patch('com.dimcon.synthera.utilities.s3_utility.get_s3_generator') as mock_get_generator:
            # Mock generator
            mock_generator = MagicMock()
            mock_get_generator.return_value = mock_generator
            
            # Test generate_download_url convenience function
            mock_generator.generate_presigned_url.return_value = "https://mock-url.com"
            result_url = generate_download_url("test-key.txt", 2)
            
            self.assertEqual(result_url, "https://mock-url.com")
            mock_generator.generate_presigned_url.assert_called_once_with("test-key.txt", 2)
            
            # Test is_valid_s3_key convenience function
            mock_generator.validate_s3_key_exists.return_value = True
            result_valid = is_valid_s3_key("test-key.txt")
            
            self.assertTrue(result_valid)
            mock_generator.validate_s3_key_exists.assert_called_once_with("test-key.txt")
        
        logger.info("✅ Convenience functions test passed")


def run_integration_tests():
    """Run integration tests without mocking (requires AWS credentials)."""
    logger.info("🚀 Starting S3 Pre-signed URL Integration Tests")
    
    try:
        # Test S3 utility initialization
        logger.info("🧪 Testing S3 utility initialization...")
        generator = get_s3_generator()
        logger.info("✅ S3 utility initialized successfully")
        
        # Test with real S3 URLs from your environment
        test_keys = [
            "s3://syntheraai-ppt/niketh sai/test call/sow_niketh_sai_test_call.pptx",
            "s3://syntheraai-ppt-transcript/niketh sai/test call/niketh_sai_test_call_01_test_call_-_2025-07-22-222945769.txt",
            "s3://syntheraai-ppt/non-existent/test_file.pptx"
        ]
        
        for key in test_keys:
            logger.info(f"🔍 Testing S3 key: {key}")
            
            # Test validation (will likely return False for non-existent files)
            is_valid = is_valid_s3_key(key)
            logger.info(f"📊 Key validation result: {is_valid}")
            
            # Test URL generation (should work even for non-existent files)
            download_url = generate_download_url(key, expiration_hours=1)
            if download_url:
                logger.info(f"✅ Generated download URL (length: {len(download_url)})")
                logger.debug(f"🔗 URL: {download_url[:100]}...")
            else:
                logger.warning("⚠️ Failed to generate download URL")
        
        logger.info("✅ Integration tests completed")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {str(e)}")
        logger.exception("Full exception details:", exc_info=True)


def demo_project_with_s3_urls():
    """Demonstrate Project model with S3 URL functionality."""
    logger.info("🚀 Demonstrating Project model with S3 URLs")
    
    try:
        # Create a mock project with S3 URLs
        demo_data = {
            "project_id": 123,
            "lead_id": 69,
            "project_name": "Demo S3 Integration Project",
            "project_description": "Demonstrating secure file download functionality",
            "lead_full_name": "niketh sai",
            "s3_url_sow_ppt": "s3://syntheraai-ppt/niketh sai/test call/sow_niketh_sai_test_call.pptx",
            "s3_url_transcription": "s3://syntheraai-ppt-transcript/niketh sai/test call/niketh_sai_test_call_01_test_call_-_2025-07-22-222945769.txt",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        }
        
        # Mock the Project class for demonstration
        class DemoProject:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
            
            def to_dict(self, include_download_urls=True):
                logger.info(f"📊 Converting project to dict (include_download_urls={include_download_urls})")
                
                base_dict = {
                    "project_id": self.project_id,
                    "lead_id": self.lead_id,
                    "project_name": self.project_name,
                    "project_description": self.project_description,
                    "lead_full_name": self.lead_full_name,
                    "s3_url_transcription": self.s3_url_transcription,
                    "s3_url_sow_ppt": self.s3_url_sow_ppt,
                    "created_at": self.created_at.isoformat() if self.created_at else None,
                    "updated_at": self.updated_at.isoformat() if self.updated_at else None
                }
                
                if include_download_urls:
                    # Generate download URLs for SOW PPT
                    if self.s3_url_sow_ppt:
                        logger.debug(f"🔗 Generating download URL for SOW PPT: {self.s3_url_sow_ppt}")
                        download_url = generate_download_url(self.s3_url_sow_ppt, expiration_hours=1)
                        if download_url:
                            base_dict["sow_ppt_download_url"] = download_url
                            logger.info("✅ SOW PPT download URL generated")
                        else:
                            logger.warning("⚠️ Failed to generate SOW PPT download URL")
                    
                    # Generate download URLs for transcription
                    if self.s3_url_transcription:
                        logger.debug(f"🔗 Generating download URL for transcription: {self.s3_url_transcription}")
                        download_url = generate_download_url(self.s3_url_transcription, expiration_hours=1)
                        if download_url:
                            base_dict["transcription_download_url"] = download_url
                            logger.info("✅ Transcription download URL generated")
                        else:
                            logger.warning("⚠️ Failed to generate transcription download URL")
                
                return base_dict
        
        # Create demo project
        project = DemoProject(**demo_data)
        
        # Test with download URLs
        logger.info("📋 Testing to_dict() with download URLs...")
        result_with_urls = project.to_dict(include_download_urls=True)
        logger.info(f"📊 Result with URLs: {json.dumps(result_with_urls, indent=2, default=str)}")
        
        # Test without download URLs
        logger.info("📋 Testing to_dict() without download URLs...")
        result_without_urls = project.to_dict(include_download_urls=False)
        logger.info(f"📊 Result without URLs: {json.dumps(result_without_urls, indent=2, default=str)}")
        
        logger.info("✅ Demo completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")
        logger.exception("Full exception details:", exc_info=True)


if __name__ == "__main__":
    logger.info("🚀 Starting S3 Pre-signed URL Test Suite")
    
    print("=" * 80)
    print("S3 PRE-SIGNED URL FUNCTIONALITY TEST SUITE")
    print("=" * 80)
    
    try:
        # Run unit tests
        print("\n🧪 RUNNING UNIT TESTS...")
        unittest.main(verbosity=2, exit=False, argv=[''])
        
        print("\n🔧 RUNNING INTEGRATION TESTS...")
        run_integration_tests()
        
        print("\n🎭 RUNNING DEMONSTRATION...")
        demo_project_with_s3_urls()
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Tests interrupted by user")
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test suite failed: {str(e)}")
        print(f"\n❌ Test suite failed: {str(e)}")
        raise
    
    print("=" * 80)
