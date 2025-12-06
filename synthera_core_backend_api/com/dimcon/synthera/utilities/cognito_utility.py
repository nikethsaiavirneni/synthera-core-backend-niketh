"""
Cognito Utility Module for handling AWS Cognito user authentication and registration.

This module provides utilities for:
- Extracting user context from API Gateway Cognito authorizer
- Auto-registering new Cognito users in the database
- Managing organization and user mappings from email domains
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests  # Add at the top if not present

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import logging
from com.dimcon.synthera.utilities.log_handler import LoggerManager
from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.resources.connect_aurora import get_engine

logger = LoggerManager.setup_logger(__name__, level=logging.DEBUG)


class CognitoUserUtility:
    """
    Utility class for handling Cognito user authentication and auto-registration.
    """
    
    def __init__(self):
        """Initialize the Cognito utility with database connection."""
        self.engine = get_engine()
        self.db_util = DBSessionUtil(self.engine)
        logger.info("CognitoUserUtility initialized successfully")

    # --- NEW: Helper to extract claims for both HTTP API and REST API Gateway ---
    def _extract_claims_from_event(self, event: dict) -> dict:
        """
        Extract Cognito claims from API Gateway event, supporting both HTTP API (v2) and REST API (v1).
        """
        rc = event.get("requestContext", {})
        # HTTP API (v2)
        http_api_claims = rc.get("authorizer", {}).get("jwt", {}).get("claims")
        if http_api_claims:
            return http_api_claims
        # REST API (v1)
        return rc.get("authorizer", {}).get("claims", {}) or {}

    # --- PATCH: Use new claim extraction and fallback email fetch ---
    def extract_user_context_from_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract user context from API Gateway authorizer context.
        Handles both HTTP API and REST API Gateway events.
        Uses access token claims, and fetches email via UserInfo if missing.
        """
        try:
            claims = self._extract_claims_from_event(event)
            if not claims or not self.validate_cognito_claims(claims):
                logger.warning("No/invalid claims")
                return None

            cognito_sub = claims.get("sub")
            username = claims.get("username") or claims.get("cognito:username")
            email = claims.get("email")  # May be absent in access token

            # If email is missing, fetch via Cognito UserInfo endpoint
            if not email:
                email = self._fetch_email_via_userinfo(event)

            # Lookup or create user context using sub (preferred) and email
            return self.get_or_create_user_context(cognito_sub, email, username)

        except Exception as e:
            logger.error(f"Error extracting user context: {str(e)}")
            logger.exception("User context extraction error details:")
            return None

    # --- NEW: Helper to fetch email via Cognito UserInfo endpoint ---
    def _fetch_email_via_userinfo(self, event) -> Optional[str]:
        """
        Fetch user's email from Cognito UserInfo endpoint using the access token from the request headers.
        Only works if the 'email' scope is present in the token.
        """
        auth = (event.get("headers") or {}).get("authorization") or (event.get("headers") or {}).get("Authorization")
        if not auth or not auth.lower().startswith("bearer "):
            logger.warning("No Bearer token found in headers for UserInfo fetch")
            return None
        access_token = auth.split(" ", 1)[1]

        domain = os.environ.get("COGNITO_DOMAIN")  # e.g., myapp.auth.us-east-1.amazoncognito.com
        if not domain:
            logger.warning("COGNITO_DOMAIN environment variable not set")
            return None

        try:
            resp = requests.get(
                f"https://{domain}/oauth2/userInfo",
                headers={"Authorization": f"Bearer {access_token}"}, timeout=5
            )
            if resp.ok:
                data = resp.json()
                return data.get("email")
            logger.warning(f"userInfo call failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"userInfo fetch error: {e}")
        return None

    # --- PATCH: Validate access token claims, not ID token ---
    def validate_cognito_claims(self, claims: Dict[str, Any]) -> bool:
        """
        Validate Cognito claims for required fields and format.
        Enforces access token structure (not ID token).
        """
        try:
            # Must be an ACCESS token
            if claims.get("token_use") != "access":
                logger.warning(f"Invalid token_use: {claims.get('token_use')}. Expected 'access'")
                return False

            # Required access-token fields
            required = ["sub", "client_id", "scope", "exp", "iat"]
            missing = [k for k in required if k not in claims]
            if missing:
                logger.warning(f"Missing required access-token claims: {missing}")
                return False

            # Optional: enforce scopes/groups for your API
            # Example: require 'api.read' in scope
            # if 'api.read' not in claims.get('scope', ''):
            #     logger.warning("Missing required scope: api.read")
            #     return False

            return True
        except Exception as e:
            logger.error(f"Error validating access token claims: {e}")
            return False

    # --- PATCH: Prefer lookup by sub, fallback to email if present ---
    def get_or_create_user_context(self, cognito_sub: str, email: Optional[str], username: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Look up user by Cognito sub (preferred), fallback to email if present.
        Auto-register if not found and email is available.
        Organization info is not used.
        """
        try:
            with self.db_util.session_scope() as session:
                from com.dimcon.synthera.resources.organization_and_employees.employees import Employee
                user = session.query(Employee).filter(Employee.cognito_sub == cognito_sub).first()
                if not user and email:
                    user = session.query(Employee).filter(Employee.emp_org_email == email).first()
                    if user and hasattr(user, 'cognito_sub') and not user.cognito_sub:
                        user.cognito_sub = cognito_sub
                        session.commit()
                if not user and email:
                    first_name, last_name = self.extract_name_from_email_or_username(email, username)
                    user = Employee.insert_table(
                        session=session,
                        emp_org_email=email,
                        employee_name=f"{first_name} {last_name}",
                        cognito_sub=cognito_sub,
                        emp_role='employee',
                        emp_status='active',
                        created_by=1,
                        updated_by=1
                    )
                if not user:
                    logger.warning(f"User not found for sub: {cognito_sub}")
                    return None
                return {
                    'user_id': user.emp_id,
                    'region': 'US',
                    'email': user.emp_org_email,
                    'cognito_sub': cognito_sub,
                    'cognito_username': username,
                    'auto_registered': getattr(user, 'auto_registered', False)
                }
        except Exception as e:
            logger.error(f"Database lookup error: {str(e)}")
            logger.exception("User lookup error details:")
            return None

    def auto_register_cognito_user(self, cognito_sub: str, email: str, username: str, 
                                  claims: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Auto-register a new Cognito user in the database.
        Organization info is not used.
        """
        try:
            with self.db_util.session_scope() as session:
                from com.dimcon.synthera.resources.organization_and_employees.employees import Employee
                logger.info(f"Auto-registering new user: {email}")
                first_name, last_name = self.extract_name_from_email_or_username(email, username)
                new_employee = Employee.insert_table(
                    session=session,
                    emp_org_email=email,
                    employee_name=f"{first_name} {last_name}",
                    cognito_sub=cognito_sub,
                    emp_role='employee',
                    emp_status='active',
                    created_by=1,
                    updated_by=1
                )
                logger.info(f"Successfully auto-registered user {email} with emp_id: {new_employee.emp_id}")
                user_context = {
                    'user_id': new_employee.emp_id,
                    'region': 'US',
                    'email': new_employee.emp_org_email,
                    'cognito_sub': cognito_sub,
                    'cognito_username': username,
                    'auto_registered': True
                }
                return user_context
        except Exception as e:
            logger.error(f"Auto-registration error for {email}: {str(e)}")
            logger.exception("Auto-registration error details:")
            return None

    def extract_name_from_email_or_username(self, email: str, username: str) -> Tuple[str, str]:
        """
        Extract first and last name from email or username.
        
        Args:
            email: User email
            username: Cognito username
            
        Returns:
            Tuple of (first_name, last_name)
        """
        try:
            # Try to extract from email local part
            local_part = email.split('@')[0]
            
            # Common patterns: firstname.lastname, firstname_lastname, firstnamelastname
            if '.' in local_part:
                parts = local_part.split('.')
                first_name = parts[0].capitalize()
                last_name = parts[-1].capitalize() if len(parts) > 1 else ''
            elif '_' in local_part:
                parts = local_part.split('_')
                first_name = parts[0].capitalize()
                last_name = parts[-1].capitalize() if len(parts) > 1 else ''
            else:
                # Use username or email local part as first name
                first_name = username.capitalize() if username else local_part.capitalize()
                last_name = ''
            
            # Fallback to defaults if empty
            if not first_name:
                first_name = username.capitalize() if username else 'User'
            # Remove fallback to 'Unknown' for last_name
            # if not last_name:
            #     last_name = 'Unknown'
            
            return first_name, last_name
            
        except Exception as e:
            logger.error(f"Error extracting name from {email}/{username}: {str(e)}")
            return 'User', ''

    def send_admin_notification(self, new_user_context: Dict[str, Any]) -> None:
        """
        Send notification to administrators about new user registration.
        
        Args:
            new_user_context: Context of newly registered user
        """
        try:
            # Create notification payload
            notification = {
                "type": "new_user_auto_registered",
                "user_email": new_user_context['email'],
                "user_id": new_user_context['user_id'],
                "cognito_sub": new_user_context['cognito_sub'],
                "timestamp": datetime.utcnow().isoformat(),
                "auto_registered": new_user_context.get('auto_registered', False)
            }
            
            logger.info(f"📧 Admin notification: New user auto-registered - {notification}")
            
            # TODO: Implement actual notification sending
            # - Send email to admins
            # - Send Slack notification
            # - Add to admin dashboard
            # - Store in notifications table
            
        except Exception as e:
            logger.error(f"Error sending admin notification: {str(e)}")

    def validate_cognito_claims(self, claims: Dict[str, Any]) -> bool:
        """
        Validate Cognito claims for required fields and format.
        
        Args:
            claims: Cognito claims dictionary
            
        Returns:
            True if claims are valid, False otherwise
        """
        try:
            # Required fields
            required_fields = ['sub', 'email', 'cognito:username']
            
            for field in required_fields:
                if field not in claims or not claims[field]:
                    logger.warning(f"Missing or empty required claim: {field}")
                    return False
            
            # Validate email format
            email = claims.get('email', '')
            if '@' not in email or '.' not in email.split('@')[1]:
                logger.warning(f"Invalid email format: {email}")
                return False
            
            # Validate token use (should be 'id' for ID tokens)
            token_use = claims.get('token_use')
            if token_use and token_use != 'id':
                logger.warning(f"Invalid token_use: {token_use}. Expected 'id'")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Cognito claims: {str(e)}")
            return False


# Convenience function for easy import
def create_cognito_utility() -> CognitoUserUtility:
    """
    Factory function to create a CognitoUserUtility instance.
    
    Returns:
        CognitoUserUtility instance
    """
    return CognitoUserUtility()


# Example usage and testing
if __name__ == "__main__":
    logger.info("Testing CognitoUserUtility")
    
    try:
        # Create utility instance
        cognito_util = CognitoUserUtility()
        
        # Sample API Gateway event for testing
        sample_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "test-user-123-456-789",
                        "email": "test.user@dimcon.com",
                        "cognito:username": "testuser",
                        "token_use": "id"
                    }
                }
            }
        }
        
        logger.info("Testing user context extraction...")
        user_context = cognito_util.extract_user_context_from_event(sample_event)
        
        if user_context:
            logger.info("✅ User context extracted successfully:")
            logger.info(f"   User ID: {user_context.get('user_id')}")
            logger.info(f"   Org ID: {user_context.get('org_id')}")
            logger.info(f"   Email: {user_context.get('email')}")
            logger.info(f"   Auto-registered: {user_context.get('auto_registered', False)}")
        else:
            logger.info("ℹ️ User context extraction returned None (user may not exist)")
        
        logger.info("✅ CognitoUserUtility testing completed")
        
    except Exception as e:
        logger.error(f"❌ Error testing CognitoUserUtility: {str(e)}")
        logger.exception("Testing error details:")
