"""
Client Module: wake_sql_client

Purpose
- Provide a reusable Python client for calling the wake-sql HTTP endpoint.
- Standardize request payload shape and response parsing for application code,
    scripts, and local diagnostics.

What this module does
1. Builds a JSON POST request for the wake-sql function.
2. Sends target instance information and polling configuration.
3. Handles SSL configuration for secure and local/dev scenarios.
4. Parses JSON responses safely, including non-JSON fallbacks.
5. Normalizes error handling for HTTP, network, and SSL failures.

Primary class
- WakeSqlFunctionClient
    Encapsulates endpoint URL, timeout settings, SSL behavior, and call logic.

Constructor fields
- function_url
    Full URL of the deployed wake-sql endpoint.
- timeout_seconds
    HTTP timeout for the client request itself.
- poll_seconds
    Value passed to server so server-side readiness polling interval is controlled.
- max_wait_seconds
    Value passed to server so server-side maximum wait is controlled.
- verify_ssl
    If False, SSL certificate verification is disabled (dev-only).
- ca_bundle_path
    Optional custom CA bundle path for environments with private CAs.

Request payload sent by call(...)
- project_id
- instance_id
- poll_seconds
- max_wait_seconds

Return contract
- Success and handled errors both return tuple[int, dict]:
    (status_code, response_payload)
- Typical values:
    - 200 for successful endpoint responses.
    - HTTP error codes (4xx/5xx) when server responded with an error.
    - 0 when request failed before receiving an HTTP response
        (for example DNS/network/SSL issues).

SSL behavior details
- verify_ssl=False:
    Uses an unverified SSL context. Use only for temporary local debugging.
- ca_bundle_path provided:
    Uses that CA bundle.
- default mode:
    Tries certifi CA bundle first; if unavailable, falls back to system CAs.

Error-handling behavior
- If server returns an HTTP error body that is JSON, it is parsed and returned.
- If body is not JSON, raw body is wrapped as {"raw_body": ...}.
- SSL certificate verification problems return a hint explaining certifi usage.

Quick usage example
- client = WakeSqlFunctionClient(function_url="https://...run.app")
- status_code, payload = client.call(
            project_id="my-project",
            instance_id="my-project:us-central1:my-instance",
    )

Operational note
- This client does not retry automatically. If retries are needed, apply them
    in the caller with backoff appropriate for your workload.
"""

import json
import ssl
from dataclasses import dataclass
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class WakeSqlFunctionClient:
    function_url: str
    timeout_seconds: int = 30
    poll_seconds: int = 5
    max_wait_seconds: int = 900
    verify_ssl: bool = True
    ca_bundle_path: Optional[str] = None

    @staticmethod
    def _parse_json_body(body):
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw_body": body}

    def _ssl_context(self):
        if not self.verify_ssl:
            return ssl._create_unverified_context()

        if self.ca_bundle_path:
            return ssl.create_default_context(cafile=self.ca_bundle_path)

        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            return ssl.create_default_context()

    def call(self, project_id, instance_id) -> tuple[int, dict]:
        payload = {
            "project_id": project_id,
            "instance_id": instance_id,
            "poll_seconds": self.poll_seconds,
            "max_wait_seconds": self.max_wait_seconds,
        }
        request = Request(
            self.function_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout_seconds,
                context=self._ssl_context(),
            ) as response:
                body = response.read().decode("utf-8")
                return response.status, self._parse_json_body(body)
        except URLError as err:
            if isinstance(err, HTTPError):
                body = err.read().decode("utf-8") if err.fp else ""
                parsed = self._parse_json_body(body)
                if parsed:
                    return err.code, parsed
                return err.code, {"error": str(err)}
            if isinstance(err.reason, ssl.SSLCertVerificationError):
                return 0, {
                    "error": "Request failed",
                    "details": str(err),
                    "hint": (
                        "SSL certificate verification failed. Install certifi and set "
                        "SSL_CERT_FILE to certifi.where(), or provide ca_bundle_path."
                    ),
                }
            return 0, {"error": "Request failed", "details": str(err)}