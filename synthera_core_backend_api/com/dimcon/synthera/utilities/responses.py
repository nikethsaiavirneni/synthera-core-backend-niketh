"""
Shared helpers for building HTTP responses in Lambda.
This class is stateless and domain‑agnostic.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

class ResponseBuilder:
    """
    A helper class for constructing HTTP responses in AWS Lambda.
    This class is designed to be stateless and domain-agnostic,
    so that it can be reused across different parts of the application.
    """

    _DEFAULT_HEADERS: dict[str, str] = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token, X-Requested-With, Accept, Origin",
        "Access-Control-Max-Age": "86400",  # Cache preflight for 24 hours
        "Access-Control-Allow-Credentials": "false",
    }

    @classmethod
    def build_response(
        cls,
        status_code: int,
        body: Mapping[str, Any] | list[Any] | str,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a standard API Gateway proxy response.

        Parameters
        ----------
        status_code : int
            HTTP status code to return.
        body : dict | list | str
            Response payload; will be JSON‑encoded.
        headers : dict[str, str] | None, optional
            Extra headers to merge with the defaults.

        Returns
        -------
        dict[str, Any]
            Dict shaped exactly as API Gateway expects.
        """
        merged_headers = {**cls._DEFAULT_HEADERS, **(headers or {})}
        return {
            "statusCode": status_code,
            "headers": merged_headers,
            "body": json.dumps(body, default=str),
        }

    @classmethod
    def build_cors_response(
        cls,
        status_code: int = 200,
        body: Mapping[str, Any] | list[Any] | str | None = None,
        origin: str = "*",
        additional_headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a CORS-enabled response specifically for preflight and cross-origin requests.

        Parameters
        ----------
        status_code : int, optional
            HTTP status code to return (default: 200).
        body : dict | list | str | None, optional
            Response payload; will be JSON‑encoded (default: {"message": "CORS OK"}).
        origin : str, optional
            Allowed origin for CORS (default: "*").
        additional_headers : dict[str, str] | None, optional
            Extra headers to include.

        Returns
        -------
        dict[str, Any]
            Dict shaped exactly as API Gateway expects with enhanced CORS headers.
        """
        cors_headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token, X-Requested-With, Accept, Origin",
            "Access-Control-Max-Age": "86400",
            "Access-Control-Allow-Credentials": "false",
            "Vary": "Origin",
        }
        
        if additional_headers:
            cors_headers.update(additional_headers)
        
        response_body = body if body is not None else {"message": "CORS OK"}
        
        return {
            "statusCode": status_code,
            "headers": cors_headers,
            "body": json.dumps(response_body, default=str),
        }
