"""Asynchroniczny klient API Pstryk.pl."""
from __future__ import annotations

import aiohttp
from typing import Any


class PstrykApiError(Exception):
    """Błąd komunikacji z API."""


class PstrykClient:
    """Minimalny klient endpointu /pricing."""

    def __init__(self, session: aiohttp.ClientSession, api_token: str) -> None:
        self._session = session
        self._token = api_token

    async def async_get_pricing(
        self, window_start: str, window_end: str, resolution: str = "hour"
    ) -> dict[str, Any]:
        """Pobiera dane pricing w formacie JSON."""
        url = "https://api.pstryk.pl/pricing"
        params = {
            "window_start": window_start,
            "window_end": window_end,
            "resolution": resolution,
        }
        headers = {"Authorization": f"Bearer {self._token}"}

        async with self._session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                raise PstrykApiError(f"HTTP {resp.status}: {await resp.text()}")
            return await resp.json()
