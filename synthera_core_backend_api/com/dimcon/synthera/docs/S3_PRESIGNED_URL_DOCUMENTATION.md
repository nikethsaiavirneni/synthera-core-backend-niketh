# S3 Pre-signed URL Implementation Documentation

## Overview

This document describes the implementation of secure S3 pre-signed URL functionality for the Synthera Core Backend API. The system enables secure file downloads without exposing internal S3 paths or requiring AWS credentials on the frontend.

## Features

### 🔐 Security Features
- **Private S3 Storage**: All files stored in private S3 buckets
- **No Direct URL Exposure**: Internal S3 keys never exposed to frontend
- **Temporary Access**: Pre-signed URLs expire after 1 hour
- **No AWS Credentials Required**: Frontend doesn't need AWS access
- **CloudTrail Logging**: Full audit trail of file access

### 📁 Supported File Types
- **SOW PowerPoint Files**: Statement of Work presentations (`s3_url_sow_ppt`)
- **Meeting Transcriptions**: Text files with meeting notes (`s3_url_transcription`)
- **Extensible**: Easy to add more file types

## Architecture

### Database Schema
```sql
-- Projects table with S3 URL columns
ALTER TABLE project_leads ADD COLUMN s3_url_sow_ppt VARCHAR(500);
ALTER TABLE project_leads ADD COLUMN s3_url_transcription VARCHAR(500);
```

### S3 URL Storage Format
```
Internal Storage (Database):
✅ "documents/projects/123/statement_of_work.pptx"
✅ "s3://synthera-documents/path/to/file.ext"

NOT Stored:
❌ "https://synthera-documents.s3.amazonaws.com/..." (public URLs)
```

### Generated Download URLs
```
Temporary Pre-signed URL:
https://synthera-documents.s3.amazonaws.com/documents/projects/123/file.ext?
AWSAccessKeyId=ASIA...&Signature=...&Expires=1642780800
```

## Implementation Components

### 1. S3 Utility (`s3_utility.py`)

**Purpose**: Central utility for S3 operations and pre-signed URL generation.

**Key Classes**:
- `S3PresignedURLGenerator`: Main class for URL generation
- `get_s3_generator()`: Singleton pattern for global access

**Key Methods**:
```python
# Generate download URL
generate_presigned_url(s3_key, expiration_hours=1)

# Validate S3 object exists
validate_s3_key_exists(s3_key)

# Get object metadata
get_object_metadata(s3_key)

# Convenience functions
generate_download_url(s3_key, expiration_hours=1)
is_valid_s3_key(s3_key)
```

### 2. Enhanced Project Model (`projects_lead.py`)

**Enhanced `to_dict()` Method**:
```python
def to_dict(self, include_download_urls=True):
    # Base project data
    base_dict = {...}
    
    # Add secure download URLs if requested
    if include_download_urls:
        if self.s3_url_sow_ppt:
            if is_valid_s3_key(self.s3_url_sow_ppt):
                base_dict["sow_ppt_download_url"] = generate_download_url(self.s3_url_sow_ppt)
        
        if self.s3_url_transcription:
            if is_valid_s3_key(self.s3_url_transcription):
                base_dict["transcription_download_url"] = generate_download_url(self.s3_url_transcription)
    
    return base_dict
```

### 3. Service Layer Integration (`projects_service.py`)

**Automatic URL Generation**: All service methods that return project data automatically include download URLs by calling `to_dict()` with default parameters.

**Methods Enhanced**:
- `get_project_by_id()`: Single project with download URLs
- `get_all_projects()`: List of projects with download URLs  
- `get_projects_by_lead_id()`: Projects by lead with download URLs
- `advanced_search_projects()`: Search results with download URLs
- `create_project()`: New project response with download URLs
- `update_project()`: Updated project response with download URLs

### 4. Configuration (`config.ini`)

```ini
[aws]
region = us-east-1

[s3]
bucket_name = synthera-documents

[database]
# ... existing database config
```

## API Response Examples

### Project with S3 Files
```json
{
  "statusCode": 200,
  "body": {
    "message": "Success",
    "data": {
      "project_id": 123,
      "project_name": "Demo Project",
      "project_description": "Project with secure file downloads",
      "lead_id": 69,
      "lead_full_name": "John Doe",
      "s3_url_sow_ppt": "documents/projects/123/sow.pptx",
      "s3_url_transcription": "documents/projects/123/transcript.txt",
      "sow_ppt_download_url": "https://synthera-documents.s3.amazonaws.com/documents/projects/123/sow.pptx?AWSAccessKeyId=ASIA...&Signature=...&Expires=1642780800",
      "transcription_download_url": "https://synthera-documents.s3.amazonaws.com/documents/projects/123/transcript.txt?AWSAccessKeyId=ASIA...&Signature=...&Expires=1642780800",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  }
}
```

### Project without S3 Files
```json
{
  "statusCode": 200,
  "body": {
    "message": "Success",
    "data": {
      "project_id": 124,
      "project_name": "Basic Project",
      "project_description": "Project without file attachments",
      "lead_id": 69,
      "lead_full_name": "John Doe",
      "s3_url_sow_ppt": null,
      "s3_url_transcription": null,
      // Note: No download URL fields included when no S3 files
      "created_at": "2025-01-15T10:35:00Z",
      "updated_at": "2025-01-15T10:35:00Z"
    }
  }
}
```

## Frontend Integration

### Download Button Implementation
```javascript
// React component example
function ProjectDownloads({ project }) {
  return (
    <div className="download-section">
      {project.sow_ppt_download_url && (
        <a 
          href={project.sow_ppt_download_url}
          download
          className="download-btn"
        >
          📄 Download Statement of Work
        </a>
      )}
      
      {project.transcription_download_url && (
        <a 
          href={project.transcription_download_url}
          download
          className="download-btn"
        >
          📝 Download Meeting Transcript
        </a>
      )}
    </div>
  );
}
```

### Error Handling
```javascript
async function downloadFile(url, filename) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Download link has expired. Please refresh the page.');
      }
      throw new Error('Failed to download file.');
    }
    
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Download failed:', error);
    alert(error.message);
  }
}
```

## Security Considerations

### ✅ Security Benefits
1. **Private Buckets**: S3 buckets remain completely private
2. **No Credential Exposure**: Frontend never needs AWS credentials
3. **Automatic Expiration**: URLs expire after 1 hour
4. **Audit Logging**: CloudTrail logs all access attempts
5. **Internal Path Protection**: Raw S3 paths never exposed
6. **Access Control**: Backend controls all file access

### 🔒 Security Best Practices
1. **Regular Key Rotation**: Rotate AWS IAM credentials regularly
2. **Least Privilege**: IAM roles have minimal required permissions
3. **HTTPS Only**: All pre-signed URLs use HTTPS
4. **Short Expiration**: Default 1-hour expiration for URLs
5. **Validation**: Always validate S3 keys before generating URLs
6. **Error Handling**: Never expose internal errors to clients

## Testing

### Unit Tests (`test_s3_presigned_urls.py`)
- S3 utility initialization
- URL generation success/failure scenarios
- S3 key validation
- Project model integration
- Error handling

### Integration Tests (`test_api_s3_integration.py`)
- End-to-end API testing
- Service layer integration
- Router layer integration
- Database integration

### Migration Script (`migrate_s3_integration.py`)
- Database schema verification
- Sample data creation
- URL format validation
- Integration summary

## Deployment Checklist

### Prerequisites
- [ ] AWS IAM role with S3 permissions
- [ ] S3 bucket created and configured
- [ ] Database columns added (`s3_url_sow_ppt`, `s3_url_transcription`)
- [ ] Configuration updated with bucket name
- [ ] boto3 dependency installed

### AWS IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:HeadObject"
      ],
      "Resource": [
        "arn:aws:s3:::synthera-documents/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::synthera-documents"
      ]
    }
  ]
}
```

### Deployment Steps
1. **Deploy Code**: Deploy updated backend code
2. **Run Migration**: Execute `migrate_s3_integration.py`
3. **Test Integration**: Run test scripts
4. **Verify URLs**: Test pre-signed URL generation
5. **Frontend Update**: Update frontend to use new download URLs
6. **Monitor**: Watch CloudTrail logs for access patterns

## Monitoring and Maintenance

### CloudWatch Metrics
- Pre-signed URL generation rate
- S3 access patterns
- Error rates for invalid keys
- URL expiration statistics

### Regular Maintenance
1. **Log Review**: Weekly review of CloudTrail logs
2. **Error Monitoring**: Monitor for 403/404 errors
3. **Performance**: Track URL generation performance
4. **Security Audit**: Monthly security review

## Troubleshooting

### Common Issues

**❌ "Failed to generate download URL"**
- Check AWS credentials and permissions
- Verify S3 bucket exists and is accessible
- Confirm IAM role has required permissions

**❌ "S3 object not found"**
- Verify S3 key format is correct
- Check if file exists in S3 bucket
- Validate bucket name in configuration

**❌ "Download link expired"**
- Normal behavior after 1 hour
- Frontend should refresh project data
- Consider implementing auto-refresh

**❌ "Access denied to S3"**
- Check IAM permissions
- Verify bucket policy allows access
- Confirm AWS credentials are valid

### Debug Commands
```bash
# Test S3 configuration
python test_s3_presigned_urls.py

# Test API integration
python test_api_s3_integration.py

# Run migration diagnostics
python migrate_s3_integration.py

# Check database schema
python -c "from migrate_s3_integration import verify_s3_columns; verify_s3_columns()"
```

## Future Enhancements

### Planned Features
1. **Multiple File Types**: Support for more document types
2. **Bulk Downloads**: ZIP file generation for multiple documents
3. **Upload URLs**: Pre-signed URLs for secure file uploads
4. **File Metadata**: Enhanced file information (size, type, etc.)
5. **Access Analytics**: Detailed download analytics
6. **Custom Expiration**: Per-file expiration settings

### Scalability Considerations
1. **CDN Integration**: CloudFront for global file distribution
2. **Caching**: Redis cache for frequently accessed URLs
3. **Async Processing**: Background URL generation for large datasets
4. **Rate Limiting**: Prevent abuse of URL generation

---

*This implementation provides a secure, scalable foundation for file downloads while maintaining strict security standards and excellent user experience.*
