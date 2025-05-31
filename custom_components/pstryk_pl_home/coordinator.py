"""DataUpdateCoordinator – pobiera dzisiejsze ceny godzinowe z Pstryk.pl."""
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
    """Koordynator odświeżający dane co n minut."""

    def __init__(self, hass: HomeAssistant, client: PstrykClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=dt.timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._client = client

    # --------------------------------------------------------------------- #
    async def _async_update_data(self) -> dict[str, Any]:
        """Pobierz dane pricing na bieżący dzień i przemapuj je na dict[HH:00]."""
        today_local = dt_util.now().date()
        start_utc = dt.datetime.combine(today_local, dt.time.min, tzinfo=dt.timezone.utc)
        end_utc = dt.datetime.combine(today_local, dt.time.max, tzinfo=dt.timezone.utc)

        _LOGGER.debug(
            "⏰ Window %s → %s (UTC)  resolution=hour", start_utc, end_utc
        )

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
            if not start_dt:
                continue

            # dt_util.as_local() od 2025.5 przyjmuje tylko jeden argument
            hour_local = dt_util.as_local(start_dt).strftime("%H:00")
            frames_hours[hour_local] = frame["price_gross"]

        _LOGGER.debug(
            "📶 Frames received: %d  (avg=%.4f PLN/kWh)",
            len(frames_hours),
            raw["price_gross_avg"],
        )

        return {
            "price_gross_avg": raw["price_gross_avg"],
            "frames_hours": frames_hours,
        }