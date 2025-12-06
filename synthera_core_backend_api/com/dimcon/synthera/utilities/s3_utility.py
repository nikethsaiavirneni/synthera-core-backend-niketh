# ================================
# S3 Utility for Pre-signed URLs
# ================================
import os
import sys

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import boto3
import configparser
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional
from datetime import timedelta

# ================================
# Centralized Logger
# ================================
from com.dimcon.synthera.utilities.log_handler import LoggerManager
import logging
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)


class S3PresignedURLGenerator:
    """
    A utility class for generating pre-signed URLs for S3 objects.
    
    This class provides secure, temporary access to private S3 files without 
    exposing AWS credentials or internal file paths to clients.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the S3 pre-signed URL generator.
        
        Args:
            config_path (str, optional): Path to configuration file. 
                                       Defaults to the project's config.ini
        """
        self.s3_client = None
        self.aws_region = None
        self.bucket_name = None
        self.ppt_bucket_name = None
        self.transcript_bucket_name = None
        self.json_bucket_name = None  # New bucket for AI JSON files
        self._load_config(config_path)
        self._initialize_s3_client()
    
    def _load_config(self, config_path: str = None):
        """Load AWS and S3 configuration from config.ini file."""
        try:
            if config_path is None:
                # Default to project's config.ini
                current_dir = os.path.dirname(__file__)
                config_path = os.path.join(current_dir, '..', 'resources', 'config.ini')
                config_path = os.path.abspath(config_path)
            
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Load AWS region
            if config.has_section('aws') and config.has_option('aws', 'region'):
                self.aws_region = config.get('aws', 'region').strip()
                logger.info("🌍 AWS region loaded: %s", self.aws_region)
            else:
                raise ValueError("AWS region not found in configuration")
            
            # Load S3 bucket names for different file types
            if config.has_section('s3'):
                # Default bucket
                if config.has_option('s3', 'bucket_name'):
                    self.bucket_name = config.get('s3', 'bucket_name').strip()
                else:
                    self.bucket_name = "synthera-documents"
                
                # PPT bucket
                if config.has_option('s3', 'ppt_bucket_name'):
                    self.ppt_bucket_name = config.get('s3', 'ppt_bucket_name').strip()
                    logger.info("📄 PPT bucket configured: %s", self.ppt_bucket_name)
                else:
                    self.ppt_bucket_name = self.bucket_name
                
                # Transcript bucket
                if config.has_option('s3', 'transcript_bucket_name'):
                    self.transcript_bucket_name = config.get('s3', 'transcript_bucket_name').strip()
                    logger.info("📝 Transcript bucket configured: %s", self.transcript_bucket_name)
                else:
                    self.transcript_bucket_name = self.bucket_name
                
                # JSON bucket for AI files
                if config.has_option('s3', 'json_bucket_name'):
                    self.json_bucket_name = config.get('s3', 'json_bucket_name').strip()
                    logger.info("🤖 JSON bucket configured: %s", self.json_bucket_name)
                else:
                    self.json_bucket_name = self.bucket_name
                
                logger.info("🪣 S3 buckets configured - Default: %s, PPT: %s, Transcript: %s, JSON: %s", 
                           self.bucket_name, self.ppt_bucket_name, self.transcript_bucket_name, self.json_bucket_name)
            else:
                # Default bucket names if not specified
                self.bucket_name = "synthera-documents"
                self.ppt_bucket_name = "syntheraai-ppt"
                self.transcript_bucket_name = "syntheraai-ppt-transcript"
                self.json_bucket_name = "syntheraai-ai-json"
                logger.warning("⚠️ S3 bucket config not found, using defaults")
                
        except Exception as e:
            logger.error("❌ Failed to load S3 configuration: %s", str(e))
            raise
    
    def _parse_s3_url(self, s3_url: str) -> tuple:
        """
        Parse S3 URL to extract bucket name and key.
        
        Args:
            s3_url (str): S3 URL in format s3://bucket/key or just the key
            
        Returns:
            tuple: (bucket_name, key) or (None, None) if invalid
        """
        if not s3_url or not s3_url.strip():
            return None, None
        
        cleaned_url = s3_url.strip()
        
        # Handle full S3 URL format: s3://bucket/key
        if cleaned_url.startswith('s3://'):
            try:
                # Remove s3:// prefix
                url_without_prefix = cleaned_url[5:]
                
                # Split into bucket and key
                if '/' in url_without_prefix:
                    bucket, key = url_without_prefix.split('/', 1)
                    logger.debug("🔍 Parsed S3 URL - Bucket: %s, Key: %s", bucket, key)
                    return bucket, key
                else:
                    logger.warning("⚠️ Invalid S3 URL format (no key): %s", cleaned_url)
                    return None, None
            except Exception as e:
                logger.error("❌ Failed to parse S3 URL: %s - %s", cleaned_url, str(e))
                return None, None
        else:
            # Handle key-only format - determine bucket based on file type/content
            key = cleaned_url
            bucket = self._determine_bucket_for_key(key)
            logger.debug("🔍 Using key with determined bucket - Bucket: %s, Key: %s", bucket, key)
            return bucket, key
    
    def _determine_bucket_for_key(self, key: str) -> str:
        """
        Determine the appropriate bucket for a given key based on file type.
        
        Args:
            key (str): The S3 object key
            
        Returns:
            str: The bucket name to use
        """
        if not key:
            return self.bucket_name
        
        key_lower = key.lower()
        
        # Check for PowerPoint files
        if any(ext in key_lower for ext in ['.pptx', '.ppt', '.ppsx', '.pps']):
            logger.debug("📄 Detected PowerPoint file, using PPT bucket")
            return self.ppt_bucket_name
        
        # Check for transcript/text files
        if any(ext in key_lower for ext in ['.txt', '.transcript', '.log']) or 'transcript' in key_lower:
            logger.debug("📝 Detected transcript file, using transcript bucket")
            return self.transcript_bucket_name
        
        # Check for JSON files (AI analysis files)
        if any(ext in key_lower for ext in ['.json', '.jsonl']) or 'ai_analysis' in key_lower or 'ai_insights' in key_lower:
            logger.debug("🤖 Detected JSON/AI file, using JSON bucket")
            return self.json_bucket_name
        
        # Default bucket for other files
        logger.debug("📁 Using default bucket for file type")
        return self.bucket_name
    
    def _initialize_s3_client(self):
        """Initialize the boto3 S3 client with proper error handling."""
        try:
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            logger.info("✅ S3 client initialized successfully")
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found. Please configure your AWS credentials.")
            raise
        except Exception as e:
            logger.error("❌ Failed to initialize S3 client: %s", str(e))
            raise
    
    def generate_presigned_url(self, 
                              s3_url: str, 
                              expiration_hours: int = 1,
                              http_method: str = 'GET') -> Optional[str]:
        """
        Generate a pre-signed URL for downloading an S3 object.
        
        Args:
            s3_url (str): The S3 URL (full s3://bucket/key format or just key)
            expiration_hours (int): Hours until the URL expires (default: 1 hour)
            http_method (str): HTTP method for the URL (default: 'GET')
            
        Returns:
            Optional[str]: Pre-signed URL if successful, None if failed
        """
        if not s3_url or not s3_url.strip():
            logger.warning("⚠️ Empty S3 URL provided, cannot generate pre-signed URL")
            return None
        
        # Parse the S3 URL to get bucket and key
        bucket_name, s3_key = self._parse_s3_url(s3_url)
        
        if not bucket_name or not s3_key:
            logger.warning("⚠️ Invalid S3 URL format: %s", s3_url)
            return None
        
        expiration_seconds = expiration_hours * 3600
        
        try:
            logger.info("🔗 Generating pre-signed URL for S3 object")
            logger.debug("📊 URL parameters - Bucket: %s, Key: %s, Expiration: %d hours", 
                        bucket_name, s3_key, expiration_hours)
            
            # Generate the pre-signed URL
            presigned_url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration_seconds,
                HttpMethod=http_method
            )
            
            logger.info("✅ Pre-signed URL generated successfully")
            logger.debug("🔗 URL length: %d characters", len(presigned_url))
            return presigned_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.warning("⚠️ S3 object not found: %s/%s", bucket_name, s3_key)
            elif error_code == 'AccessDenied':
                logger.error("❌ Access denied to S3 object: %s/%s", bucket_name, s3_key)
            else:
                logger.error("❌ S3 ClientError (%s): %s", error_code, str(e))
            return None
            
        except Exception as e:
            logger.error("❌ Unexpected error generating pre-signed URL: %s", str(e))
            logger.exception("Full exception details:", exc_info=True)
            return None
    
    def validate_s3_key_exists(self, s3_url: str) -> bool:
        """
        Check if an S3 object exists without downloading it.
        
        Args:
            s3_url (str): The S3 URL (full s3://bucket/key format or just key)
            
        Returns:
            bool: True if object exists, False otherwise
        """
        if not s3_url or not s3_url.strip():
            return False
        
        # Parse the S3 URL to get bucket and key
        bucket_name, s3_key = self._parse_s3_url(s3_url)
        
        if not bucket_name or not s3_key:
            return False
        
        try:
            logger.debug("🔍 Checking if S3 object exists: %s/%s", bucket_name, s3_key)
            self.s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            logger.debug("✅ S3 object exists: %s/%s", bucket_name, s3_key)
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.debug("📭 S3 object not found: %s/%s", bucket_name, s3_key)
            else:
                logger.warning("⚠️ Error checking S3 object existence (%s): %s", 
                             error_code, str(e))
            return False
            
        except Exception as e:
            logger.error("❌ Unexpected error checking S3 object: %s", str(e))
            return False
    
    def get_object_metadata(self, s3_url: str) -> Optional[dict]:
        """
        Get metadata for an S3 object.
        
        Args:
            s3_url (str): The S3 URL (full s3://bucket/key format or just key)
            
        Returns:
            Optional[dict]: Object metadata if successful, None if failed
        """
        if not s3_url or not s3_url.strip():
            return None
        
        # Parse the S3 URL to get bucket and key
        bucket_name, s3_key = self._parse_s3_url(s3_url)
        
        if not bucket_name or not s3_key:
            return None
        
        try:
            logger.debug("📊 Getting S3 object metadata: %s/%s", bucket_name, s3_key)
            response = self.s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            
            metadata = {
                'content_length': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', 'unknown'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'bucket': bucket_name,
                'key': s3_key
            }
            
            logger.debug("✅ S3 metadata retrieved for: %s/%s", bucket_name, s3_key)
            return metadata
            
        except ClientError as e:
            logger.warning("⚠️ Failed to get S3 metadata: %s", str(e))
            return None
            
        except Exception as e:
            logger.error("❌ Unexpected error getting S3 metadata: %s", str(e))
            return None


# ================================
# Singleton Pattern for Global Use
# ================================
_s3_generator_instance = None

def get_s3_generator() -> S3PresignedURLGenerator:
    """
    Get a singleton instance of the S3 pre-signed URL generator.
    
    Returns:
        S3PresignedURLGenerator: The singleton instance
    """
    global _s3_generator_instance
    if _s3_generator_instance is None:
        _s3_generator_instance = S3PresignedURLGenerator()
    return _s3_generator_instance


# ================================
# Convenience Functions
# ================================
def generate_download_url(s3_url: str, expiration_hours: int = 1) -> Optional[str]:
    """
    Convenience function to generate a download URL for an S3 object.
    
    Args:
        s3_url (str): The S3 URL (full s3://bucket/key format or just key)
        expiration_hours (int): Hours until expiration (default: 1)
        
    Returns:
        Optional[str]: Pre-signed download URL or None if failed
    """
    try:
        generator = get_s3_generator()
        return generator.generate_presigned_url(s3_url, expiration_hours)
    except Exception as e:
        logger.error("❌ Failed to generate download URL: %s", str(e))
        return None


def is_valid_s3_key(s3_url: str) -> bool:
    """
    Check if an S3 URL is valid and the object exists.
    
    Args:
        s3_url (str): The S3 URL (full s3://bucket/key format or just key)
        
    Returns:
        bool: True if valid and exists, False otherwise
    """
    try:
        generator = get_s3_generator()
        return generator.validate_s3_key_exists(s3_url)
    except Exception as e:
        logger.error("❌ Failed to validate S3 key: %s", str(e))
        return False
