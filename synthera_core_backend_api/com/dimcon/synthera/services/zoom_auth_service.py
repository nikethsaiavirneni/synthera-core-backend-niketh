# com/dimcon/synthera/services/zoom_auth_service.py
import os
import json
import base64
import logging
import time
from urllib.parse import quote_plus

import requests

from com.dimcon.synthera.utilities.responses import ResponseBuilder

from com.dimcon.synthera.utilities.sessions_manager import DBSessionUtil
from com.dimcon.synthera.resources.connect_aurora import get_engine
from com.dimcon.synthera.utilities.cognito_utility import CognitoUserUtility
from synthera_core_backend_api.com.dimcon.synthera.resources.integration.zoom_user_config import ZoomUserConfig

engine = get_engine()
db_util = DBSessionUtil(engine)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Optional env fallbacks
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_REDIRECT_URI = os.getenv("ZOOM_REDIRECT_URI")


class ZoomAuthService:
    # -----------------------------
    # Public route (only one): /zoom/setup
    # -----------------------------
    @classmethod
    def route_setup(cls, event: dict):
        """
        POST /zoom/setup
        Save user Zoom app creds and return authorization_url in one call.
        Body JSON:
          {
            "app_user_id": "...",               # optional if JWT/header provided
            "zoom_client_id": "...",
            "zoom_client_secret": "...",
            "zoom_redirect_uri": "https://..."
          }
        """
        try:
            body = json.loads(event.get("body") or "{}")
        except Exception:
            body = {}

        app_user_id = (body.get("app_user_id") or cls._resolve_app_user_id(event))
        client_id = body.get("zoom_client_id")
        client_secret = body.get("zoom_client_secret")
        redirect_uri = body.get("zoom_redirect_uri")

        missing = [k for k, v in {
            "app_user_id": app_user_id,
            "zoom_client_id": client_id,
            "zoom_client_secret": client_secret,
            "zoom_redirect_uri": redirect_uri,
        }.items() if not v]
        if missing:
            return ResponseBuilder.build_response(400, {"error": "Missing required fields", "fields": missing})

        # Persist config and return auth URL (state carries app_user_id)
        cls.save_zoom_config(app_user_id, client_id, client_secret, redirect_uri, event=event)
        url = cls.get_authorization_url(app_user_id)
        return ResponseBuilder.build_response(200, {"message": "Saved", "authorization_url": url})

    # -----------------------------
    # Config
    # -----------------------------

    @classmethod
    def get_user_zoom_config(cls, app_user_id):
        # DB first, then env
        from com.dimcon.synthera.resources.integration.zoom_user_config import ZoomUserConfig
        print(f"[PRINT] get_user_zoom_config: app_user_id={app_user_id}")
        logger.debug(f"[ZoomAuthService.get_user_zoom_config] Fetching config for app_user_id: {app_user_id}")
        try:
            with db_util.session_scope() as session:
                cfg = session.query(ZoomUserConfig).filter_by(app_user_id=app_user_id).first()
                if cfg:
                    return (
                        getattr(cfg, "zoom_client_id", None),
                        getattr(cfg, "zoom_client_secret", None),
                        getattr(cfg, "zoom_redirect_uri", None),
                    )
        except Exception as e:
            logger.error(f"Error fetching Zoom config: {e}")
        return ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_REDIRECT_URI

    @classmethod
    def save_zoom_config(cls, app_user_id, client_id, client_secret, redirect_uri, event=None):
        from com.dimcon.synthera.resources.integration.zoom_user_config import ZoomUserConfig
        from com.dimcon.synthera.resources.organization_and_employees.employees import Employee

        print(f"[PRINT] save_zoom_config: app_user_id={app_user_id}")
        logger.debug(f"[ZoomAuthService.save_zoom_config] Saving config for app_user_id: {app_user_id}")
        # Use Cognito utility to get or create employee
        emp_id = None
        if event:
            cognito_util = CognitoUserUtility()
            user_context = cognito_util.extract_user_context_from_event(event)
            if user_context:
                emp_id = user_context['user_id']

        with db_util.session_scope() as session:
            cfg = session.query(ZoomUserConfig).filter_by(app_user_id=app_user_id).first()
            if not cfg:
                cfg = ZoomUserConfig(app_user_id=app_user_id)
                session.add(cfg)
            cfg.zoom_client_id = client_id
            cfg.zoom_client_secret = client_secret
            cfg.zoom_redirect_uri = redirect_uri
            if emp_id:
                cfg.created_by = emp_id
                cfg.updated_by = emp_id
            return {"message": "Zoom app configuration saved successfully", "data": {
                "app_user_id": app_user_id,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }}

    @classmethod
    def save_oauth_tokens(cls, app_user_id, tokens):
        from com.dimcon.synthera.resources.integration.zoom_user_config import ZoomUserConfig
        with db_util.session_scope() as session:
            cfg = session.query(ZoomUserConfig).filter_by(app_user_id=app_user_id).first()
            if not cfg:
                cfg = ZoomUserConfig(app_user_id=app_user_id)
                session.add(cfg)
            cfg.zoom_user_id = tokens.get("zoom_user_id")
            cfg.access_token = tokens.get("access_token")
            cfg.refresh_token = tokens.get("refresh_token")
            cfg.token_type = tokens.get("token_type")
            cfg.expires_in = tokens.get("expires_in")
            cfg.scope = tokens.get("scope")

    @classmethod
    def get_oauth_tokens(cls, app_user_id):
        try:
            with db_util.session_scope() as session:
                cfg = session.query(ZoomUserConfig).filter_by(app_user_id=app_user_id).first()
                if not cfg:
                    return None
                return {
                    "zoom_user_id": getattr(cfg, "zoom_user_id", None),
                    "access_token": getattr(cfg, "access_token", None),
                    "refresh_token": getattr(cfg, "refresh_token", None),
                    "token_type": getattr(cfg, "token_type", None),
                    "expires_in": getattr(cfg, "expires_in", None),
                    "scope": getattr(cfg, "scope", None),
                }
        except Exception as e:
            logger.error(f"Error fetching OAuth tokens: {e}")
            return None

    # -----------------------------
    # OAuth core (internal)
    # -----------------------------
    @classmethod
    def get_authorization_url(cls, app_user_id, state=None, code_challenge=None, code_challenge_method="S256"):
        client_id, _, redirect_uri = cls.get_user_zoom_config(app_user_id)
        if not client_id or not redirect_uri:
            raise RuntimeError("Zoom app configuration not found. Please configure your Zoom app credentials first.")
        _state = state or app_user_id
        url = (
            "https://zoom.us/oauth/authorize"
            f"?response_type=code&client_id={client_id}"
            f"&redirect_uri={quote_plus(redirect_uri)}"
            f"&state={quote_plus(_state)}"
        )
        if code_challenge:
            url += f"&code_challenge={quote_plus(code_challenge)}&code_challenge_method={quote_plus(code_challenge_method)}"
        return url

    @classmethod
    def handle_oauth_callback(cls, code, app_user_id, code_verifier=None):
        """
        Kept internal so your OAuth redirect target can still call it
        (even if you don't expose a router path).
        Exchanges code -> tokens, stores zoom_user_id/tokens.
        """
        client_id, client_secret, redirect_uri = cls.get_user_zoom_config(app_user_id)
        if not all([client_id, client_secret, redirect_uri]):
            raise RuntimeError("Zoom app configuration not found. Please configure your Zoom app credentials first.")

        token_url = "https://zoom.us/oauth/token"
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
        if code_verifier:
            data["code_verifier"] = code_verifier

        resp = requests.post(token_url, headers=headers, data=data)
        resp.raise_for_status()
        tokens = resp.json()

        # Fetch user for zoom_user_id
        access_token = tokens.get("access_token")
        user_info = _zoom_request("GET", "https://api.zoom.us/v2/users/me",
                                  headers={"Authorization": f"Bearer {access_token}"}).json()

        ZoomAuthService.save_oauth_tokens(app_user_id, {
            "zoom_user_id": user_info.get("id"),
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "token_type": tokens.get("token_type", "Bearer"),
            "expires_in": tokens.get("expires_in"),
            "scope": tokens.get("scope"),
        })
        return {"message": "Zoom account connected successfully."}

    @classmethod
    def _refresh_access_token(cls, app_user_id):
        tokens = ZoomAuthService.get_oauth_tokens(app_user_id) or {}
        rtoken = tokens.get("refresh_token")
        if not rtoken:
            raise RuntimeError("No refresh token available; re-authentication required.")
        client_id, client_secret, _ = cls.get_user_zoom_config(app_user_id)
        token_url = "https://zoom.us/oauth/token"
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "refresh_token", "refresh_token": rtoken}
        resp = requests.post(token_url, headers=headers, data=data)
        if resp.status_code != 200:
            raise RuntimeError(f"Token refresh failed ({resp.status_code}): {resp.text}")
        new = resp.json()
        new["zoom_user_id"] = new.get("zoom_user_id") or tokens.get("zoom_user_id")
        ZoomAuthService.save_oauth_tokens(app_user_id, new)
        return new.get("access_token")

    @classmethod
    def get_access_token_and_user(cls, app_user_id):
        tokens = ZoomAuthService.get_oauth_tokens(app_user_id)
        if not tokens or not tokens.get("access_token"):
            raise RuntimeError("User has not connected their Zoom account.")
        if not tokens.get("zoom_user_id"):
            # Fix missing user id on the fly
            access = tokens["access_token"]
            ui = _zoom_request("GET", "https://api.zoom.us/v2/users/me",
                               headers={"Authorization": f"Bearer {access}"}).json()
            tokens["zoom_user_id"] = ui.get("id")
            ZoomAuthService.save_oauth_tokens(app_user_id, tokens)
        return tokens["access_token"], tokens["zoom_user_id"]

    # -----------------------------
    # Cross-service helpers
    # -----------------------------
    @staticmethod
    def _resolve_app_user_id(event: dict):
        rc = event.get("requestContext") or {}
        auth = rc.get("authorizer") or {}
        claims = (auth.get("jwt") or {}).get("claims", {}) or auth.get("claims", {}) or {}
        uid = claims.get("email") or claims.get("sub")
        if uid:
            return uid
        headers = event.get("headers") or {}
        dev = headers.get("X-App-User-Id") or headers.get("x-app-user-id")
        if dev:
            return dev
        qs = event.get("queryStringParameters") or {}
        if qs.get("app_user_id"):
            return qs["app_user_id"]
        try:
            body = json.loads(event.get("body") or "{}")
            if body.get("app_user_id"):
                return body["app_user_id"]
        except Exception:
            pass
        return None


# -----------------------------
# Module-level HTTP helper (shared)
# -----------------------------
def _zoom_request(method, url, headers=None, json=None, data=None, tries=3):
    for i in range(tries):
        resp = requests.request(method, url, headers=headers, json=json, data=data, timeout=15)
        if resp.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
            time.sleep(2 ** i)
            continue
        return resp

