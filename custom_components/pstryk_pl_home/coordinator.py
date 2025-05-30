"""DataUpdateCoordinator do pobierania cen godzinowych."""
from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant

from .api import PstrykClient, PstrykApiError
from .const import DOMAIN, SCAN_INTERVAL_MINUTES


class PstrykCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordynator pobierający dzisiejsze ceny godzinowe."""

    def __init__(self, hass: HomeAssistant, client: PstrykClient) -> None:
        super().__init__(
            hass,
            _LOGGER,  # _LOGGER pochodzi z core; nie wymaga importu w tym miejscu
            name=DOMAIN,
            update_interval=dt.timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Pobiera i formatuje dane."""
        # okno: 00:00–23:59:59 lokalnie → UTC
        today_local = dt_util.now().date()
        start_utc = dt.datetime.combine(today_local, dt.time.min, tzinfo=dt.timezone.utc)
        end_utc = dt.datetime.combine(
            today_local, dt.time.max.replace(microsecond=0), tzinfo=dt.timezone.utc
        )

        try:
            raw = await self._client.async_get_pricing(
                window_start=start_utc.isoformat(timespec="seconds"),
                window_end=end_utc.isoformat(timespec="seconds"),
                resolution="hour",
            )
        except PstrykApiError as err:
            raise UpdateFailed(err) from err

        # Konwersja ramek na słownik {'HH:00': cena_gross}
        frames_hours = {}
        tz = dt_util.get_time_zone(self.hass.config.time_zone)
        for frame in raw["frames"]:
            hour_local = (
                dt_util.as_local(dt_util.parse_datetime(frame["start"]), tz)
                .strftime("%H:00")
            )
            frames_hours[hour_local] = frame["price_gross"]

        return {
            "price_gross_avg": raw["price_gross_avg"],
            "frames_hours": frames_hours,
        }
