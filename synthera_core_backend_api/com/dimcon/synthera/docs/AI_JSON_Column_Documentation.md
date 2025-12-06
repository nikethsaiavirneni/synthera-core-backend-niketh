# AI JSON Column Documentation

## Overview
The `s3_url_ai_json` column has been added to the `project_leads` table to store S3 file paths for AI-generated JSON files containing analysis, insights, or other AI-processed data.

## Features

### 🗃️ Database Column
- **Column Name**: `s3_url_ai_json`
- **Type**: `VARCHAR(500)`
- **Nullable**: `YES`
- **Purpose**: Store S3 file paths for AI-generated JSON files

### 🪣 S3 Bucket Routing
- **JSON Files**: Automatically routed to `syntheraai-ai-json` bucket
- **Supported Extensions**: `.json`, `.jsonl`
- **Auto-detection**: Files with "ai_analysis" or "ai_insights" in the path
- **Configuration**: Configured in `config.ini` under `[s3]` section

### 🔗 Pre-signed URL Generation
- **Secure Downloads**: Generate time-limited download URLs (1 hour expiration)
- **Dynamic Generation**: URLs are generated on-demand in API responses
- **Error Handling**: Graceful handling of missing files
- **Response Field**: `ai_json_download_url` in project API responses

## Usage Examples

### 1. Creating a Project with AI JSON
```python
project_data = {
    "lead_id": 69,
    "project_name": "AI Analysis Project",
    "project_description": "Project with AI insights",
    "s3_url_ai_json": "documents/projects/69/ai_analysis.json"
}

project_id = Project.insert_table(**project_data)
```

### 2. Retrieving Project with Download URLs
```python
project = Project.get_by_id(project_id)
project_dict = project.to_dict(include_download_urls=True)

# Access the AI JSON download URL
if "ai_json_download_url" in project_dict:
    download_url = project_dict["ai_json_download_url"]
    print(f"AI JSON download URL: {download_url}")
```

### 3. API Response Example
```json
{
  "project_id": 67,
  "lead_id": 69,
  "project_name": "AI Analysis Project",
  "project_description": "Project with AI insights",
  "lead_full_name": "niketh sai",
  "s3_url_transcription": null,
  "s3_url_sow_ppt": null,
  "s3_url_ai_json": "documents/projects/69/ai_analysis.json",
  "created_at": "2025-07-30T04:16:22+00:00",
  "updated_at": "2025-07-30T04:16:22+00:00",
  "ai_json_download_url": "https://syntheraai-ai-json.s3.amazonaws.com/documents/projects/69/ai_analysis.json?..."
}
```

## S3 Bucket Configuration

### config.ini
```ini
[s3]
bucket_name = synthera-documents
ppt_bucket_name = syntheraai-ppt
transcript_bucket_name = syntheraai-ppt-transcript
json_bucket_name = syntheraai-ai-json
```

### Bucket Routing Logic
1. **PowerPoint files** (`.pptx`, `.ppt`) → `syntheraai-ppt`
2. **Transcript files** (`.txt`, `.log`, or "transcript" in name) → `syntheraai-ppt-transcript`
3. **JSON files** (`.json`, `.jsonl`, or "ai_analysis"/"ai_insights" in name) → `syntheraai-ai-json`
4. **Other files** → `synthera-documents` (default)

## File Path Examples

### Recommended Path Structure
```
documents/projects/{project_id}/ai_analysis_{project_id}.json
documents/projects/{project_id}/ai_insights_{timestamp}.json
documents/projects/{project_id}/ai_report_{lead_name}.json
```

### Sample Paths
- `documents/projects/1/ai_analysis_1.json`
- `documents/projects/2/ai_insights_2025-07-30.json`
- `documents/projects/3/ai_report_niketh_sai.json`
- `documents/projects/4/ai_summary.jsonl`

## API Integration

### Projects API Endpoints
All existing projects API endpoints now support the AI JSON field:

- **GET** `/projects` - Lists all projects with AI JSON URLs
- **GET** `/projects/{id}` - Gets single project with AI JSON URL
- **POST** `/projects` - Create project with AI JSON path
- **PUT** `/projects/{id}` - Update project AI JSON path
- **DELETE** `/projects/{id}` - Delete project (including AI JSON reference)

### Search Support
The AI JSON column is searchable through the advanced search functionality:
```
GET /projects?filter_s3_url_ai_json__contains=ai_analysis
GET /projects?search=ai_insights
```

## Security Considerations

### Pre-signed URLs
- ✅ **Time-limited**: URLs expire after 1 hour
- ✅ **No exposed credentials**: AWS credentials not exposed to clients
- ✅ **Dynamic generation**: URLs generated fresh for each request
- ✅ **Access control**: Only valid S3 objects get URLs

### File Validation
- ✅ **Existence check**: Validates S3 object exists before generating URL
- ✅ **Error handling**: Graceful handling of missing files
- ✅ **Bucket routing**: Automatic routing to correct bucket based on file type

## Testing

### Run Tests
```bash
# Test AI JSON functionality
python com/dimcon/synthera/scripts/test_ai_json_functionality.py

# Test bucket routing
python -c "
from com.dimcon.synthera.utilities.s3_utility import S3PresignedURLGenerator
s3 = S3PresignedURLGenerator()
print(s3._determine_bucket_for_key('documents/projects/1/ai_analysis.json'))
"
```

### Test Results
- ✅ Column creation successful
- ✅ Bucket routing working correctly
- ✅ Data insertion with AI JSON paths working
- ✅ Download URL generation working
- ✅ Multi-file support (PPT, transcript, AI JSON) working

## Migration

### Database Migration
The `s3_url_ai_json` column has been added using:
```sql
ALTER TABLE project_leads 
ADD COLUMN IF NOT EXISTS s3_url_ai_json VARCHAR(500);
```

### Backward Compatibility
- ✅ **Existing data**: All existing projects continue to work
- ✅ **Optional field**: AI JSON column is nullable
- ✅ **API compatibility**: Existing API calls continue to work
- ✅ **Legacy support**: Existing S3 URLs for PPT and transcripts unchanged

## Future Enhancements

### Potential Improvements
1. **Multiple AI JSON files**: Support for multiple AI analysis files per project
2. **AI file types**: Support for other AI-generated file types (CSV, XML, etc.)
3. **AI metadata**: Additional columns for AI processing metadata
4. **Versioning**: Support for versioned AI analysis files
5. **AI processing status**: Track processing status of AI files

### Monitoring
- Monitor S3 bucket usage for `syntheraai-ai-json`
- Track download URL generation success rates
- Monitor file access patterns for optimization

---

## Summary

The AI JSON column functionality is now fully implemented and tested:

1. ✅ **Database column** added successfully
2. ✅ **S3 bucket routing** configured for JSON files
3. ✅ **Pre-signed URL generation** working securely
4. ✅ **API integration** complete with backward compatibility
5. ✅ **Search functionality** supports AI JSON column
6. ✅ **Testing** confirms all functionality works correctly

Your projects can now store and securely serve AI-generated JSON files alongside existing PowerPoint presentations and transcripts!
