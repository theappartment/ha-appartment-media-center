"""Authenticated local API client. Never expose the token to the frontend."""
from datetime import datetime, timedelta, timezone
import ssl
from urllib.parse import urlsplit
from uuid import uuid4

import aiohttp


class ApiError(Exception):
    """Communication or protocol failure."""


class AuthenticationError(ApiError):
    """Invalid API credentials."""


def normalize_url(value):
    """Accept an HTTPS origin, never embedded credentials or query parameters."""
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path):
        raise ValueError("Use an HTTPS origin, for example https://appartment.local:8443")
    _ = parsed.port  # Validate port syntax/range.
    return value


def make_ssl_context(ca_file=""):
    """Called in an executor: reading CA files must not block HA's event loop."""
    return ssl.create_default_context(cafile=ca_file or None)


def validate_state(data):
    if (not isinstance(data, dict) or not isinstance(data.get("device_id"), str)
            or not data["device_id"] or not isinstance(data.get("requested_mode"), str)):
        raise ApiError("Risposta di stato non valida")
    return data


class MediaCenterApi:
    def __init__(self, session, url, token, ssl_context):
        self.session = session
        self.url = normalize_url(url)
        self._token = token
        self._ssl = ssl_context

    async def _request(self, method, path, payload=None):
        try:
            async with self.session.request(
                method, self.url + "/api/v1/" + path,
                headers={"Authorization": f"Bearer {self._token}"},
                json=payload, ssl=self._ssl, allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status in (401, 403):
                    raise AuthenticationError("Token API non valido")
                if not 200 <= response.status < 300:
                    raise ApiError(f"Il media center ha risposto HTTP {response.status}")
                data = await response.json()
                if not isinstance(data, dict):
                    raise ApiError("Risposta API non valida")
                return data
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            # Do not log response bodies/headers, which may contain sensitive data.
            raise ApiError("Connessione, certificato TLS o risposta JSON non validi") from err

    async def status(self):
        return validate_state(await self._request("GET", "status"))

    async def set_mode(self, mode):
        result = await self._request("POST", "commands", {
            "id": str(uuid4()),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat(),
            "action": "set_mode", "args": {"mode": mode},
        })
        if result.get("status") != "applied":
            raise ApiError("Il media center non ha applicato il comando")
        return validate_state(result.get("state"))
