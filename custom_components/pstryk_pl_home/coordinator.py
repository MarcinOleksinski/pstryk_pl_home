"""DataUpdateCoordinator – pobiera dzienny cennik godzinowy z Pstryk.pl."""
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
        self._tz = dt_util.get_time_zone(hass.config.time_zone)

    # ------------------------------------------------------------------ #
    async def _async_update_data(self) -> dict[str, Any]:
        """Pobierz ceny na lokalny dzień (00-24) – okno w UTC."""
        today_local = dt_util.now(self._tz).date()

        # 00:00 lokalnie → UTC
        local_midnight = dt.datetime.combine(today_local, dt.time.min, tzinfo=self._tz)
        start_utc = local_midnight.astimezone(dt.timezone.utc)

        # 23:59:59 lokalnie → UTC
        local_end = dt.datetime.combine(
            today_local, dt.time(hour=23, minute=59, second=59), tzinfo=self._tz
        )
        end_utc = local_end.astimezone(dt.timezone.utc)

        _LOGGER.debug(
            "⏰ Window local [%s → %s]  UTC [%s → %s]",
            local_midnight,
            local_end,
            start_utc,
            end_utc,
        )

        try:
            raw = await self._client.async_get_pricing(
                window_start=start_utc.isoformat(timespec="seconds"),
                window_end=end_utc.isoformat(timespec="seconds"),
                resolution="hour",
            )
        except PstrykApiError as err:
            raise UpdateFailed(err) from err

        # mapuj ramki → {"HH:00": cena_gross}
        frames_hours: dict[str, float] = {}
        for frame in raw["frames"]:
            start_dt = dt_util.parse_datetime(frame["start"])
            if not start_dt:
                continue
            hour_local = dt_util.as_local(start_dt).strftime("%H:00")
            frames_hours[hour_local] = frame["price_gross"]

        _LOGGER.debug(
            "📶 Frames: %d  avg=%.4f",
            len(frames_hours),
            raw["price_gross_avg"],
        )

        return {
            "price_gross_avg": raw["price_gross_avg"],
            "frames_hours": frames_hours,
        }