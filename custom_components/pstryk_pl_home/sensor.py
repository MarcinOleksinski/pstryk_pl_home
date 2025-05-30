"""Sensory Pstryk.pl – ceny godzinowe dzisiejszego dnia."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ENTITY_PREFIX
from .coordinator import PstrykCoordinator

_SENSOR_KEY = "prices_today"


class PstrykPriceTodaySensor(CoordinatorEntity[PstrykCoordinator], SensorEntity):
    """Średnia cena energii za bieżący dzień + ceny wszystkich godzin w atrybucie."""

    _attr_has_entity_name = True
    _attr_name = "Pstryk – średnia dzisiaj"
    _attr_native_unit_of_measurement = "PLN/kWh"
    _attr_state_class = "measurement"
    _attr_icon = "mdi:currency-usd"  # brak dedykowanej ikony PLN

    def __init__(self, coordinator: PstrykCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)

        prefix: str = entry.data[CONF_ENTITY_PREFIX]
        self._attr_unique_id = f"{prefix}_{_SENSOR_KEY}"
        self.entity_id = f"sensor.{prefix}_{_SENSOR_KEY}"

    @property
    def native_value(self) -> Decimal:
        """Zwróć średnią cenę brutto (Decimal)."""
        return Decimal(self.coordinator.data["price_gross_avg"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atrybut `hours` – mapa 'HH:00' → cena brutto."""
        return {"hours": self.coordinator.data["frames_hours"]}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zarejestruj encje sensorów dla danego wpisu."""
    coordinator: PstrykCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PstrykPriceTodaySensor(coordinator, entry)], True)