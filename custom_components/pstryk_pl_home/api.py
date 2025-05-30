"""Asynchroniczny klient API Pstryk.pl."""
from __future__ import annotations

from typing import Any
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

API_URL = "https://api.pstryk.pl/v1/pricing"   # <-- 404 znika po poprawnym URL-u


class PstrykApiError(Exception):
    """Błąd odpowiedzi API."""


class PstrykClient:
    """Klient endpointu /pricing."""

    def __init__(self, session: aiohttp.ClientSession, api_token: str) -> None:
        self._session = session
        self._token = api_token

    async def async_get_pricing(
        self,
        *,
        window_start: str,
        window_end: str,
        resolution: str = "hour",
    ) -> dict[str, Any]:
        params = {
            "window_start": window_start,
            "window_end": window_end,
            "resolution": resolution,
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

        _LOGGER.debug("GET %s %s", API_URL, params)

        async with self._session.get(API_URL, params=params, headers=headers) as resp:
            text = await resp.text()
            if resp.status == 404:
                raise PstrykApiError("endpoint_not_found")
            if resp.status == 401:
                raise PstrykApiError("invalid_auth")
            if resp.status != 200:
                _LOGGER.error("Pstryk API %s: %s", resp.status, text)
                raise PstrykApiError(f"HTTP {resp.status}")

            return await resp.json()