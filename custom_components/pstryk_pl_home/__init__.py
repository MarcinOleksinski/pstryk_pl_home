"""Inicjalizacja integracji Pstryk.pl Home."""
from __future__ import annotations
import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, CONF_API_TOKEN
from .api import PstrykClient
from .coordinator import PstrykCoordinator
from .sensor import PstrykPriceTodaySensor

_LOGGER = logging.getLogger(__name__)


async def async_setup(_: HomeAssistant, __: dict) -> bool:
    """Konfiguracja przez YAML (nieobsługiwana)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup po dodaniu w WebUI."""
    session = aiohttp_client.async_get_clientsession(hass)
    client = PstrykClient(session, entry.data[CONF_API_TOKEN])

    coordinator = PstrykCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # rejestruj encje
    hass.helpers.discovery.async_load_platform(
        "sensor", DOMAIN, {"entry": entry}, entry.data
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    coordinator: PstrykCoordinator | None = hass.data[DOMAIN].pop(entry.entry_id, None)
    if coordinator:
        await coordinator.async_shutdown()
    return True
