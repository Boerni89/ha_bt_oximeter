from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OximeterBluetoothCoordinator
from .device_base import OximeterMeasurement


@dataclass
class OximeterSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[OximeterMeasurement | None], Any] = lambda _: None


SENSORS: list[OximeterSensorEntityDescription] = [
    OximeterSensorEntityDescription(
        key="spo2",
        translation_key="spo2",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-percent",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.spo2 if data else None,
    ),
    OximeterSensorEntityDescription(
        key="pulse_rate",
        translation_key="pulse_rate",
        native_unit_of_measurement="bpm",
        icon="mdi:heart-pulse",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.pulse if data else None,
    ),
    OximeterSensorEntityDescription(
        key="perfusion_index",
        translation_key="perfusion_index",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.perfusion_index if data else None,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OximeterBluetoothCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[OximeterSensorEntity] = [
        OximeterSensorEntity(coordinator, entry.entry_id, description)
        for description in SENSORS
    ]
    async_add_entities(entities)


class OximeterSensorEntity(
    CoordinatorEntity[OximeterBluetoothCoordinator], SensorEntity
):
    """Sensor-Entity für einen Messwert des Oxymeters."""

    entity_description: OximeterSensorEntityDescription

    def __init__(
        self,
        coordinator: OximeterBluetoothCoordinator,
        entry_id: str,
        description: OximeterSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_has_entity_name = True

        self._attr_unique_id = f"{entry_id}_{description.key}"

        # Get device info from coordinator's device instance
        device_info = coordinator.device.device_info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            name="Pulse Oximeter",
            manufacturer=device_info.manufacturer,
            model=device_info.model,
        )

    @property
    def native_value(self) -> Any:
        data: OximeterMeasurement | None = self.coordinator.data
        return self.entity_description.value_fn(data)
