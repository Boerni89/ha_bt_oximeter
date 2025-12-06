from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OximeterBluetoothCoordinator
from .device_base import OximeterMeasurement


BINARY_SENSORS: list[BinarySensorEntityDescription] = [
    BinarySensorEntityDescription(
        key="finger",
        translation_key="finger",
        icon="mdi:hand-back-right",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OximeterBluetoothCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[OximeterFingerEntity] = [
        OximeterFingerEntity(coordinator, entry.entry_id, description)
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)


class OximeterFingerEntity(CoordinatorEntity[OximeterBluetoothCoordinator], BinarySensorEntity):
    """Binary-Sensor für 'Finger im Gerät'."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: OximeterBluetoothCoordinator,
        entry_id: str,
        description: BinarySensorEntityDescription,
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
    def is_on(self) -> bool | None:
        data: OximeterMeasurement | None = self.coordinator.data
        if data is None:
            return None
        return data.finger_present
