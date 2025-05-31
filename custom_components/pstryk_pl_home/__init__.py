"""Inicjalizacja integracji Pstryk.pl Home (z dodatkowymi logami DEBUG)."""
from __future__ import annotations

import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, CONF_API_TOKEN
from .api import PstrykClient
from .coordinator import PstrykCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(_: HomeAssistant, __: dict) -> bool:
    """Konfiguracja przez YAML – nieużywana."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Uruchom integrację po dodaniu w UI."""
    _LOGGER.debug("⏩ async_setup_entry: start (entry_id=%s)", entry.entry_id)

    session: aiohttp.ClientSession = aiohttp_client.async_get_clientsession(hass)
    client = PstrykClient(session, entry.data[CONF_API_TOKEN])

    coordinator = PstrykCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.debug("📊 Initial coordinator data: %s", coordinator.data)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # forwarduj do platformy sensor
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    _LOGGER.debug("✅ Forwarded to sensor platform (entry_id=%s)", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    _LOGGER.debug("⏬ async_unload_entry (entry_id=%s)", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok