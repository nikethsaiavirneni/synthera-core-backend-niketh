#!/usr/bin/env python3
"""
Database Migration Script: Add s3_url_ai_json column to project_leads table

This script adds the new s3_url_ai_json column to the existing project_leads table.
Run this script after updating the Project model to ensure the database schema is synchronized.

Usage:
    python add_ai_json_column_migration.py

Features:
- ✅ Safe migration with rollback capability
- ✅ Checks if column already exists before adding
- ✅ Comprehensive logging
- ✅ Sample data insertion for testing
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import text, inspect
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.log_handler import LoggerManager
import logging

# Setup logger
logger = LoggerManager.setup_logger(__name__, level=logging.INFO)

class AIJsonColumnMigration:
    """Migration class for adding s3_url_ai_json column"""
    
    def __init__(self):
        self.engine = get_engine()
        self.table_name = "project_leads"
        self.new_column_name = "s3_url_ai_json"
        
    def check_column_exists(self):
        """Check if the s3_url_ai_json column already exists"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(self.table_name)
            column_names = [col['name'] for col in columns]
            
            exists = self.new_column_name in column_names
            logger.info(f"🔍 Column '{self.new_column_name}' exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"❌ Error checking column existence: {str(e)}")
            return False
    
    def add_column(self):
        """Add the s3_url_ai_json column to the project_leads table"""
        try:
            logger.info(f"🚀 Starting migration: Adding column '{self.new_column_name}' to '{self.table_name}' table")
            
            # Check if column already exists
            if self.check_column_exists():
                logger.info(f"✅ Column '{self.new_column_name}' already exists. Migration not needed.")
                return True
            
            # Add the new column
            alter_statement = f"""
            ALTER TABLE {self.table_name} 
            ADD COLUMN {self.new_column_name} VARCHAR(500)
            """
            
            with self.engine.connect() as connection:
                connection.execute(text(alter_statement))
                connection.commit()
                
            logger.info(f"✅ Successfully added column '{self.new_column_name}' to '{self.table_name}' table")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding column: {str(e)}")
            return False
    
    def update_sample_data(self):
        """Update some existing records with sample AI JSON paths"""
        try:
            logger.info("📝 Updating sample records with AI JSON file paths...")
            
            # Sample update queries
            sample_updates = [
                {
                    "project_id": 1,
                    "ai_json_path": "documents/projects/1/ai_analysis_project_1.json"
                },
                {
                    "project_id": 2, 
                    "ai_json_path": "documents/projects/2/ai_insights_project_2.json"
                }
            ]
            
            with self.engine.connect() as connection:
                for update_data in sample_updates:
                    # Check if project exists first
                    check_query = text(f"SELECT project_id FROM {self.table_name} WHERE project_id = :project_id")
                    result = connection.execute(check_query, {"project_id": update_data["project_id"]})
                    
                    if result.fetchone():
                        # Update existing project
                        update_query = text(f"""
                        UPDATE {self.table_name} 
                        SET {self.new_column_name} = :ai_json_path,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE project_id = :project_id
                        """)
                        
                        connection.execute(update_query, {
                            "project_id": update_data["project_id"],
                            "ai_json_path": update_data["ai_json_path"]
                        })
                        
                        logger.info(f"✅ Updated project {update_data['project_id']} with AI JSON path")
                    else:
                        logger.info(f"⏭️ Project {update_data['project_id']} not found, skipping")
                
                connection.commit()
                
            logger.info("✅ Sample data update completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating sample data: {str(e)}")
            return False
    
    def rollback_migration(self):
        """Rollback the migration by dropping the column"""
        try:
            logger.info(f"🔄 Rolling back migration: Removing column '{self.new_column_name}' from '{self.table_name}' table")
            
            if not self.check_column_exists():
                logger.info(f"✅ Column '{self.new_column_name}' doesn't exist. Rollback not needed.")
                return True
            
            # Drop the column
            alter_statement = f"""
            ALTER TABLE {self.table_name} 
            DROP COLUMN {self.new_column_name}
            """
            
            with self.engine.connect() as connection:
                connection.execute(text(alter_statement))
                connection.commit()
                
            logger.info(f"✅ Successfully removed column '{self.new_column_name}' from '{self.table_name}' table")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during rollback: {str(e)}")
            return False
    
    def validate_migration(self):
        """Validate that the migration was successful"""
        try:
            logger.info("🔍 Validating migration...")
            
            # Check column exists
            if not self.check_column_exists():
                logger.error("❌ Migration validation failed: Column not found")
                return False
            
            # Check column properties
            inspector = inspect(self.engine)
            columns = inspector.get_columns(self.table_name)
            
            ai_json_column = None
            for col in columns:
                if col['name'] == self.new_column_name:
                    ai_json_column = col
                    break
            
            if ai_json_column:
                logger.info(f"✅ Column details: {ai_json_column}")
                logger.info("✅ Migration validation successful")
                return True
            else:
                logger.error("❌ Migration validation failed: Column details not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during validation: {str(e)}")
            return False

def main():
    """Main migration execution"""
    logger.info("🚀 Starting AI JSON Column Migration")
    logger.info("=" * 60)
    
    migration = AIJsonColumnMigration()
    
    try:
        # Run the migration
        if migration.add_column():
            logger.info("✅ Column addition successful")
            
            # Validate the migration
            if migration.validate_migration():
                logger.info("✅ Migration validation successful")
                
                # Update sample data
                migration.update_sample_data()
                
                logger.info("=" * 60)
                logger.info("🎉 Migration completed successfully!")
                logger.info("💡 Next steps:")
                logger.info("   1. Deploy your updated Project model")
                logger.info("   2. Test the new AI JSON functionality")
                logger.info("   3. Update your API documentation")
                
            else:
                logger.error("❌ Migration validation failed")
                return False
        else:
            logger.error("❌ Column addition failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {str(e)}")
        logger.info("🔄 Attempting rollback...")
        migration.rollback_migration()
        return False
    
    return True

def rollback():
    """Rollback the migration"""
    logger.info("🔄 Starting Migration Rollback")
    logger.info("=" * 60)
    
    migration = AIJsonColumnMigration()
    success = migration.rollback_migration()
    
    if success:
        logger.info("✅ Rollback completed successfully")
    else:
        logger.error("❌ Rollback failed")
    
    return success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI JSON Column Migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = main()
    
    sys.exit(0 if success else 1)
