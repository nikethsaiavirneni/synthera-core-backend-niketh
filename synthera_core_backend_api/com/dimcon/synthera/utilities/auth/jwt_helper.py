# ================================
# Add project root to sys.path
# ================================
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ================================
# Standard library imports
# ================================
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import re

# ================================
# Project-specific imports
# ================================
import logging
from com.dimcon.synthera.utilities.log_handler import LoggerManager
logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)

# ================================
# JWT Authentication Utilities
# ================================
class JWTAuthHelper:
    """
    Helper class for JWT token validation and user context extraction.
    Supports RS256 signature verification and basic JWT structure validation.
    """
    
    @staticmethod
    def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT payload without signature verification (for development/testing).
        In production, this should include proper signature verification.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dictionary or None if invalid
        """
        logger.debug("Decoding JWT payload")
        
        try:
            # Split the JWT into parts
            parts = token.split('.')
            if len(parts) != 3:
                logger.warning("Invalid JWT format - wrong number of parts")
                return None
            
            # Decode the payload (second part)
            payload_part = parts[1]
            
            # Add padding if needed for base64 decoding
            missing_padding = len(payload_part) % 4
            if missing_padding:
                payload_part += '=' * (4 - missing_padding)
            
            # Decode base64
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            logger.debug(f"JWT payload decoded successfully")
            return payload
            
        except Exception as e:
            logger.error(f"Error decoding JWT payload: {str(e)}")
            return None

    @staticmethod
    def validate_jwt_structure(payload: Dict[str, Any]) -> bool:
        """
        Validate that JWT payload has required structure and claims.
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            True if valid structure, False otherwise
        """
        try:
            # Check for required claims
            required_claims = ['sub', 'exp', 'iat']
            for claim in required_claims:
                if claim not in payload:
                    logger.warning(f"Missing required JWT claim: {claim}")
                    return False
            
            # Check expiration
            exp = payload.get('exp', 0)
            current_time = datetime.now(timezone.utc).timestamp()
            
            if exp < current_time:
                logger.warning("JWT token has expired")
                return False
            
            logger.debug("JWT structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating JWT structure: {str(e)}")
            return False

    @staticmethod
    def extract_user_context(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract user context information from JWT payload.
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            User context dictionary with user_id, org_id, region, etc.
        """
        logger.debug("Extracting user context from JWT payload")
        
        try:
            # Extract basic user information
            user_context = {
                'user_id': None,
                'org_id': None,
                'region': None,
                'email': None,
                'roles': [],
                'permissions': []
            }
            
            # Map common JWT claims to user context
            # Subject (sub) typically contains user ID
            user_context['user_id'] = payload.get('sub')
            
            # Look for organization ID in various possible claim names
            user_context['org_id'] = (
                payload.get('org_id') or 
                payload.get('organization_id') or 
                payload.get('org') or
                payload.get('organization')
            )
            
            # Look for region information
            user_context['region'] = (
                payload.get('region') or 
                payload.get('locale') or
                payload.get('country')
            )
            
            # Extract email
            user_context['email'] = payload.get('email')
            
            # Extract roles (can be array or comma-separated string)
            roles = payload.get('roles', [])
            if isinstance(roles, str):
                user_context['roles'] = [r.strip() for r in roles.split(',')]
            elif isinstance(roles, list):
                user_context['roles'] = roles
            
            # Extract permissions
            permissions = payload.get('permissions', [])
            if isinstance(permissions, str):
                user_context['permissions'] = [p.strip() for p in permissions.split(',')]
            elif isinstance(permissions, list):
                user_context['permissions'] = permissions
            
            # Extract custom claims that might contain user info
            for key in ['user_metadata', 'app_metadata', 'custom_claims']:
                if key in payload and isinstance(payload[key], dict):
                    metadata = payload[key]
                    # Override with more specific values if available
                    for field in ['user_id', 'org_id', 'region']:
                        if field in metadata and not user_context[field]:
                            user_context[field] = metadata[field]
            
            logger.debug(f"Extracted user context: user_id={user_context['user_id']}, "
                        f"org_id={user_context['org_id']}, region={user_context['region']}")
            
            return user_context
            
        except Exception as e:
            logger.error(f"Error extracting user context: {str(e)}")
            return None

    @staticmethod
    def extract_auth_header(event: Dict[str, Any]) -> Optional[str]:
        """
        Extract JWT token from API Gateway event headers.
        
        Args:
            event: API Gateway event
            
        Returns:
            JWT token string or None if not found
        """
        logger.debug("Extracting authorization header from event")
        
        try:
            headers = event.get('headers', {})
            
            # Look for Authorization header (case-insensitive)
            auth_header = None
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    auth_header = value
                    break
            
            if not auth_header:
                logger.warning("No Authorization header found")
                return None
            
            # Extract Bearer token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
                logger.debug("JWT token extracted from Authorization header")
                return token
            else:
                logger.warning("Authorization header does not contain Bearer token")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting auth header: {str(e)}")
            return None

    @staticmethod
    def authenticate_request(event: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Authenticate an API Gateway request and extract user context.
        
        Args:
            event: API Gateway event
            
        Returns:
            Tuple of (is_authenticated, user_context, error_message)
        """
        logger.debug("Starting request authentication")
        
        try:
            # Extract JWT token
            token = JWTAuthHelper.extract_auth_header(event)
            if not token:
                return False, None, "Missing or invalid Authorization header"
            
            # Decode JWT payload
            payload = JWTAuthHelper.decode_jwt_payload(token)
            if not payload:
                return False, None, "Invalid JWT token format"
            
            # Validate JWT structure
            if not JWTAuthHelper.validate_jwt_structure(payload):
                return False, None, "Invalid or expired JWT token"
            
            # Extract user context
            user_context = JWTAuthHelper.extract_user_context(payload)
            if not user_context:
                return False, None, "Could not extract user context from token"
            
            # Basic validation of required fields
            if not user_context.get('user_id'):
                return False, None, "Missing user ID in token"
            
            logger.info(f"Request authenticated successfully for user: {user_context['user_id']}")
            return True, user_context, ""
            
        except Exception as e:
            logger.error(f"Error during request authentication: {str(e)}")
            logger.exception("Authentication error details:")
            return False, None, "Authentication failed due to internal error"

# ================================
# Authorization Utilities
# ================================
class AuthorizationHelper:
    """
    Helper class for role-based and permission-based authorization.
    """
    
    @staticmethod
    def check_permission(user_context: Dict[str, Any], required_permission: str) -> bool:
        """
        Check if user has the required permission.
        
        Args:
            user_context: User context from JWT
            required_permission: Permission string to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            permissions = user_context.get('permissions', [])
            has_permission = required_permission in permissions
            
            logger.debug(f"Permission check for '{required_permission}': {has_permission}")
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission: {str(e)}")
            return False

    @staticmethod
    def check_role(user_context: Dict[str, Any], required_role: str) -> bool:
        """
        Check if user has the required role.
        
        Args:
            user_context: User context from JWT
            required_role: Role string to check
            
        Returns:
            True if user has role, False otherwise
        """
        try:
            roles = user_context.get('roles', [])
            has_role = required_role in roles
            
            logger.debug(f"Role check for '{required_role}': {has_role}")
            return has_role
            
        except Exception as e:
            logger.error(f"Error checking role: {str(e)}")
            return False

    @staticmethod
    def check_org_access(user_context: Dict[str, Any], resource_org_id: str) -> bool:
        """
        Check if user has access to resources from the specified organization.
        
        Args:
            user_context: User context from JWT
            resource_org_id: Organization ID of the resource
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            user_org_id = user_context.get('org_id')
            
            # Users can only access resources from their own organization
            has_access = user_org_id == resource_org_id
            
            logger.debug(f"Org access check - user_org: {user_org_id}, "
                        f"resource_org: {resource_org_id}, access: {has_access}")
            return has_access
            
        except Exception as e:
            logger.error(f"Error checking org access: {str(e)}")
            return False

# ================================
# Mock JWT for Development/Testing
# ================================
class MockJWTHelper:
    """
    Helper class for generating mock JWT tokens for development and testing.
    DO NOT USE IN PRODUCTION.
    """
    
    @staticmethod
    def create_mock_token(user_id: str, org_id: str, region: str = "US-NY", 
                         roles: list = None, email: str = None) -> str:
        """
        Create a mock JWT token for development/testing.
        
        Args:
            user_id: User identifier
            org_id: Organization identifier
            region: User's region
            roles: List of user roles
            email: User email
            
        Returns:
            Mock JWT token string
        """
        logger.warning("Creating MOCK JWT token - DO NOT USE IN PRODUCTION")
        
        import time
        
        payload = {
            'sub': user_id,
            'org_id': org_id,
            'region': region,
            'email': email or f"user{user_id}@example.com",
            'roles': roles or ['user'],
            'permissions': ['calendar:read', 'calendar:write'],
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,  # 1 hour expiry
            'iss': 'synthera-mock',
            'aud': 'synthera-api'
        }
        
        # Create a simple base64-encoded "token" (NOT a real JWT)
        payload_json = json.dumps(payload)
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
        
        # Mock JWT format: header.payload.signature
        mock_header = base64.urlsafe_b64encode(json.dumps({'typ': 'JWT', 'alg': 'RS256'}).encode()).decode()
        mock_signature = base64.urlsafe_b64encode(b'mock-signature').decode()
        
        mock_token = f"{mock_header}.{payload_b64}.{mock_signature}"
        
        logger.debug(f"Created mock token for user {user_id} in org {org_id}")
        return mock_token

# ================================
# Main Script Execution
# ================================
if __name__ == "__main__":
    logger.info("Testing JWT authentication utilities")
    
    try:
        # Create a mock token for testing
        mock_token = MockJWTHelper.create_mock_token(
            user_id="12345",
            org_id="org-uuid-123",
            region="US-NY",
            roles=["admin", "calendar_manager"],
            email="admin@example.com"
        )
        print(f"Mock token: {mock_token[:50]}...")
        
        # Test decoding
        payload = JWTAuthHelper.decode_jwt_payload(mock_token)
        if payload:
            print(f"Decoded payload: {json.dumps(payload, indent=2)}")
            
            # Test context extraction
            context = JWTAuthHelper.extract_user_context(payload)
            print(f"User context: {json.dumps(context, indent=2)}")
        
        logger.info("JWT utilities test completed successfully")
        
    except Exception as e:
        logger.error(f"Error testing JWT utilities: {str(e)}")
        logger.exception("Test error details:")
        raise
