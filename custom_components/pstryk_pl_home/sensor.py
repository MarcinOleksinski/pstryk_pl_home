"""Sensor średniej ceny dzisiejszej z atrybutem wszystkich godzin."""
from __future__ import annotations
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENTITY_PREFIX
from .coordinator import PstrykCoordinator

SENSOR_KEY = "prices_today"


class PstrykPriceTodaySensor(CoordinatorEntity[PstrykCoordinator], SensorEntity):
    """Encja z atrybutem 'hours'."""

    _attr_has_entity_name = True
    _attr_name = "Pstryk – średnia dzisiaj"
    _attr_native_unit_of_measurement = "PLN/kWh"
    _attr_state_class = "measurement"

    def __init__(self, coordinator: PstrykCoordinator, entry) -> None:
        super().__init__(coordinator)
        prefix: str = entry.data[CONF_ENTITY_PREFIX]
        self._attr_unique_id = f"{prefix}_{SENSOR_KEY}"
        self.entity_id = f"sensor.{prefix}_{SENSOR_KEY}"

    @property
    def native_value(self) -> Decimal:
        return Decimal(self.coordinator.data["price_gross_avg"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"hours": self.coordinator.data["frames_hours"]}
