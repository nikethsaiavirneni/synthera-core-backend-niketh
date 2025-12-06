#!/usr/bin/env python3
"""
Database migration script to add project_description column to project_leads table
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from com.dimcon.synthera.resources.connect_aurora import get_engine
from sqlalchemy import text

def run_migration():
    """Run the database migration to add project_description column"""
    try:
        # Create database engine
        engine = get_engine()
        
        # Read the migration SQL
        sql_file_path = os.path.join(project_root, 'add_project_description_column.sql')
        with open(sql_file_path, 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        with engine.connect() as connection:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.strip():
                    print(f"Executing: {statement[:100]}..." if len(statement) > 100 else f"Executing: {statement}")
                    try:
                        result = connection.execute(text(statement))
                        connection.commit()
                        print("✅ Success")
                        
                        # If it's a SELECT statement, print results
                        if statement.strip().upper().startswith('SELECT'):
                            rows = result.fetchall()
                            for row in rows:
                                print(f"  {row}")
                                
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        if "duplicate_column" not in str(e):
                            raise
        
        print("\n🎉 Migration completed successfully!")
        print("The project_description column has been added to the project_leads table.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Running database migration to add project_description column...")
    run_migration()
