-- Add s3_url_ai_json column to project_leads table
-- This script adds the new column for storing AI-generated JSON file paths

-- Add the new column
ALTER TABLE project_leads 
ADD COLUMN s3_url_ai_json VARCHAR(500);

-- Add a comment for documentation
COMMENT ON COLUMN project_leads.s3_url_ai_json IS 'S3 file path for AI-generated JSON analysis files';

-- Optional: Update existing records with sample data (uncomment if needed)
-- UPDATE project_leads 
-- SET s3_url_ai_json = 'documents/projects/' || project_id || '/ai_analysis_' || project_id || '.json'
-- WHERE s3_url_ai_json IS NULL AND project_id <= 5;

-- Verify the column was added
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns 
WHERE table_name = 'project_leads' 
AND column_name = 's3_url_ai_json';
