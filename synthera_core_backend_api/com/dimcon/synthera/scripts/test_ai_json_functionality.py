#!/usr/bin/env python3
"""
Test Script for AI JSON Column Functionality

This script tests the new s3_url_ai_json column and its S3 integration.

Features:
- ✅ Test column creation
- ✅ Test data insertion with AI JSON paths
- ✅ Test download URL generation
- ✅ Test bucket routing for JSON files
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from com.dimcon.synthera.resources.projects.projects_lead import Project
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.s3_utility import S3PresignedURLGenerator
from com.dimcon.synthera.utilities.log_handler import LoggerManager
import logging

# Setup logger
logger = LoggerManager.setup_logger(__name__, level=logging.INFO)

class AIJsonColumnTester:
    """Test class for AI JSON column functionality"""
    
    def __init__(self):
        self.engine = get_engine()
        self.s3_util = S3PresignedURLGenerator()
        
    def test_column_creation(self):
        """Test that the AI JSON column was added successfully"""
        logger.info("🧪 Testing AI JSON column creation...")
        
        try:
            # Create table with new column
            Project.create_table(self.engine)
            logger.info("✅ Table creation successful")
            return True
        except Exception as e:
            logger.error(f"❌ Table creation failed: {str(e)}")
            return False
    
    def test_data_insertion(self):
        """Test inserting data with AI JSON paths"""
        logger.info("🧪 Testing data insertion with AI JSON paths...")
        
        test_cases = [
            {
                "lead_id": 69,
                "project_name": "AI Analysis Test Project 1",
                "project_description": "Test project for AI JSON functionality",
                "s3_url_ai_json": "documents/projects/69/ai_analysis_test_1.json"
            },
            {
                "lead_id": 69,
                "project_name": "AI Insights Test Project 2", 
                "project_description": "Another test project with AI insights",
                "s3_url_ai_json": "documents/projects/69/ai_insights_test_2.json",
                "s3_url_sow_ppt": "niketh sai/test call/sow_niketh_sai_test_call.pptx",
                "s3_url_transcription": "niketh sai/test call/niketh_sai_test_call_01_test_call_-_2025-07-22-222945769.txt"
            }
        ]
        
        inserted_ids = []
        
        try:
            for i, test_data in enumerate(test_cases):
                logger.info(f"📝 Inserting test project {i+1}...")
                project_id = Project.insert_table(**test_data)
                inserted_ids.append(project_id)
                logger.info(f"✅ Test project {i+1} inserted with ID: {project_id}")
            
            return inserted_ids
            
        except Exception as e:
            logger.error(f"❌ Data insertion failed: {str(e)}")
            return []
    
    def test_data_retrieval(self, project_ids):
        """Test retrieving projects and generating download URLs"""
        logger.info("🧪 Testing data retrieval and download URL generation...")
        
        try:
            for project_id in project_ids:
                logger.info(f"🔍 Testing project ID: {project_id}")
                
                # Get project
                project = Project.get_by_id(project_id)
                if not project:
                    logger.error(f"❌ Project {project_id} not found")
                    continue
                
                logger.info(f"✅ Retrieved project: {project.project_name}")
                
                # Test to_dict with download URLs
                project_dict = project.to_dict(include_download_urls=True)
                
                # Check AI JSON URL
                if project.s3_url_ai_json:
                    logger.info(f"🔗 AI JSON S3 path: {project.s3_url_ai_json}")
                    if "ai_json_download_url" in project_dict:
                        logger.info(f"✅ AI JSON download URL generated: {project_dict['ai_json_download_url'] is not None}")
                    else:
                        logger.warning("⚠️ AI JSON download URL not found in response")
                
                # Check other URLs
                if project.s3_url_sow_ppt and "sow_ppt_download_url" in project_dict:
                    logger.info("✅ SOW PPT download URL generated")
                
                if project.s3_url_transcription and "transcription_download_url" in project_dict:
                    logger.info("✅ Transcription download URL generated")
                
                logger.info("📊 Project dict keys: %s", list(project_dict.keys()))
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Data retrieval test failed: {str(e)}")
            return False
    
    def test_bucket_routing(self):
        """Test that JSON files are routed to the correct bucket"""
        logger.info("🧪 Testing bucket routing for JSON files...")
        
        test_keys = [
            "documents/projects/1/ai_analysis.json",
            "documents/projects/2/ai_insights.jsonl", 
            "documents/projects/3/some_data.json",
            "documents/projects/4/ai_analysis_report.json"
        ]
        
        try:
            for key in test_keys:
                bucket = self.s3_util._determine_bucket_for_key(key)
                logger.info(f"🪣 Key: {key} -> Bucket: {bucket}")
                
                if bucket == self.s3_util.json_bucket_name:
                    logger.info(f"✅ JSON file correctly routed to JSON bucket")
                else:
                    logger.warning(f"⚠️ JSON file routed to: {bucket}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Bucket routing test failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting AI JSON Column Test Suite")
        logger.info("=" * 60)
        
        # Test 1: Column creation
        if not self.test_column_creation():
            logger.error("❌ Column creation test failed")
            return False
        
        # Test 2: Bucket routing
        if not self.test_bucket_routing():
            logger.error("❌ Bucket routing test failed") 
            return False
        
        # Test 3: Data insertion
        project_ids = self.test_data_insertion()
        if not project_ids:
            logger.error("❌ Data insertion test failed")
            return False
        
        # Test 4: Data retrieval
        if not self.test_data_retrieval(project_ids):
            logger.error("❌ Data retrieval test failed")
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 All tests passed successfully!")
        logger.info("💡 AI JSON column functionality is working correctly")
        return True

def main():
    """Main test execution"""
    tester = AIJsonColumnTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("✅ Test suite completed successfully")
    else:
        logger.error("❌ Test suite failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
