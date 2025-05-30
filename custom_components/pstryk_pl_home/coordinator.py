"""DataUpdateCoordinator pobierający dzisiejsze ceny godzinowe z Pstryk.pl."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PstrykClient, PstrykApiError
from .const import DOMAIN, SCAN_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class PstrykCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordynator odświeżający co 30-min cennik na bieżący dzień."""

    def __init__(self, hass: HomeAssistant, client: PstrykClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=dt.timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._client = client
        self._tz = dt_util.get_time_zone(hass.config.time_zone)

    async def _async_update_data(self) -> dict[str, Any]:
        """Pobierz dane i przemapuj je na { 'HH:00': price_gross }."""
        today_local = dt_util.now().date()
        start_utc = dt.datetime.combine(today_local, dt.time.min, tzinfo=dt.timezone.utc)
        end_utc = dt.datetime.combine(today_local, dt.time.max, tzinfo=dt.timezone.utc)

        try:
            raw = await self._client.async_get_pricing(
                window_start=start_utc.isoformat(timespec="seconds"),
                window_end=end_utc.isoformat(timespec="seconds"),
                resolution="hour",
            )
        except PstrykApiError as err:
            raise UpdateFailed(err) from err

        frames_hours: dict[str, float] = {}
        for frame in raw["frames"]:
            start_dt = dt_util.parse_datetime(frame["start"])
            if start_dt is None:
                continue
            hour_local = dt_util.as_local(start_dt, self._tz).strftime("%H:00")
            frames_hours[hour_local] = frame["price_gross"]

        return {
            "price_gross_avg": raw["price_gross_avg"],
            "frames_hours": frames_hours,
        }