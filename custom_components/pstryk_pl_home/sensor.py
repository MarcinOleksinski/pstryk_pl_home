"""Sensor: średnia cena energii za bieżący dzień + ceny godzinowe (z logami DEBUG)."""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ENTITY_PREFIX
from .coordinator import PstrykCoordinator

_LOGGER = logging.getLogger(__name__)

_SENSOR_KEY = "prices_today"


class PstrykPriceTodaySensor(CoordinatorEntity[PstrykCoordinator], SensorEntity):
    """Encja z atrybutem 'hours'."""

    _attr_has_entity_name = True
    _attr_name = "Pstryk – średnia dzisiaj"
    _attr_native_unit_of_measurement = "PLN/kWh"
    _attr_state_class = "measurement"
    _attr_icon = "mdi:currency-usd"

    def __init__(self, coordinator: PstrykCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)

        prefix: str = entry.data[CONF_ENTITY_PREFIX]
        self._attr_unique_id = f"{prefix}_{_SENSOR_KEY}"
        self.entity_id = f"sensor.{prefix}_{_SENSOR_KEY}"

        _LOGGER.debug("🆕 Creating sensor %s (unique_id=%s)", self.entity_id, self.unique_id)

    async def async_added_to_hass(self) -> None:
        """Wywoływane, gdy encja zostanie dodana do HA."""
        await super().async_added_to_hass()
        _LOGGER.debug("➕ Sensor %s added to Home Assistant", self.entity_id)

    async def _handle_coordinator_update(self) -> None:
        """Loguj każdą aktualizację danych koordynatora."""
        _LOGGER.debug(
            "🔄 Coordinator update → %s (avg=%.4f)",
            self.entity_id,
            self.coordinator.data.get("price_gross_avg"),
        )
        await super()._handle_coordinator_update()

    # ---------- wartości stanu ---------- #
    @property
    def native_value(self) -> Decimal:
        return Decimal(self.coordinator.data["price_gross_avg"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"hours": self.coordinator.data["frames_hours"]}


# ---------- setup platform ---------- #
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Rejestruj encje dla wpisu konfiguracyjnego."""
    coordinator: PstrykCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensor = PstrykPriceTodaySensor(coordinator, entry)
    async_add_entities([sensor], True)
    _LOGGER.debug("📥 Entity registered: %s", sensor.entity_id)