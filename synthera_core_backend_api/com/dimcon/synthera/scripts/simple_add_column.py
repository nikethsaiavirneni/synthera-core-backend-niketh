#!/usr/bin/env python3
"""
Simple script to add the s3_url_ai_json column to project_leads table
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import text
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.log_handler import LoggerManager
import logging

# Setup logger
logger = LoggerManager.setup_logger(__name__, level=logging.INFO)

def add_ai_json_column():
    """Add the s3_url_ai_json column to project_leads table"""
    try:
        engine = get_engine()
        
        # SQL to add the column
        add_column_sql = """
        ALTER TABLE project_leads 
        ADD COLUMN IF NOT EXISTS s3_url_ai_json VARCHAR(500);
        """
        
        logger.info("🚀 Adding s3_url_ai_json column to project_leads table...")
        
        with engine.connect() as connection:
            connection.execute(text(add_column_sql))
            connection.commit()
            
        logger.info("✅ Column added successfully!")
        
        # Verify the column was added
        verify_sql = """
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'project_leads' 
        AND column_name = 's3_url_ai_json';
        """
        
        with engine.connect() as connection:
            result = connection.execute(text(verify_sql))
            row = result.fetchone()
            
            if row:
                logger.info("✅ Column verification successful:")
                logger.info(f"   Column: {row[0]}")
                logger.info(f"   Type: {row[1]}")
                logger.info(f"   Max Length: {row[2]}")
                logger.info(f"   Nullable: {row[3]}")
                return True
            else:
                logger.error("❌ Column verification failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error adding column: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Starting column addition process")
    success = add_ai_json_column()
    
    if success:
        logger.info("🎉 Process completed successfully!")
        logger.info("💡 You can now use the s3_url_ai_json column in your Project model")
    else:
        logger.error("❌ Process failed")
        
    sys.exit(0 if success else 1)
