"""Diagnostics support for Bluetooth Oximeter."""

from __future__ import annotations

from typing import Any

from homeassistant.components import bluetooth
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OximeterBluetoothCoordinator

TO_REDACT = {"address", "unique_id", "name"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: OximeterBluetoothCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Collect device info
    device_info = coordinator.device.device_info

    # Collect current measurement data
    measurement = coordinator.data
    measurement_data = None
    if measurement:
        measurement_data = {
            "spo2": measurement.spo2,
            "pulse": measurement.pulse,
            "perfusion_index": measurement.perfusion_index,
            "finger_present": measurement.finger_present,
            "timestamp": measurement.timestamp.isoformat()
            if measurement.timestamp
            else None,
        }

    # Collect buffer information from device
    buffer_info = coordinator.device.get_buffer_info()

    # Collect last measurement (even if current is None)
    last_measurement_data = None
    if coordinator.device.last_measurement:
        last_measurement_data = {
            "spo2": coordinator.device.last_measurement.spo2,
            "pulse": coordinator.device.last_measurement.pulse,
            "perfusion_index": coordinator.device.last_measurement.perfusion_index,
            "finger_present": coordinator.device.last_measurement.finger_present,
            "timestamp": coordinator.device.last_measurement.timestamp.isoformat(),
        }

    # Collect BLE connection info
    ble_device = bluetooth.async_ble_device_from_address(
        hass, coordinator.address, connectable=True
    )
    ble_info = None
    if ble_device:
        ble_info = {
            "name": async_redact_data({"name": ble_device.name}, TO_REDACT).get("name"),
            "address": async_redact_data(
                {"address": ble_device.address}, TO_REDACT
            ).get("address"),
        }

    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
        },
        "device": {
            "manufacturer": device_info.manufacturer,
            "model": device_info.model,
            "frame_header": device_info.frame_header.hex(),
            "frame_length": device_info.frame_length,
            "notify_uuid": device_info.notify_uuid,
            "supported_ouis": device_info.supported_ouis,
        },
        "coordinator": {
            "available": coordinator.available,
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "connection": coordinator.get_connection_info(),
        "bluetooth_device": ble_info,
        "current_measurement": measurement_data,
        "last_measurement": last_measurement_data,
        "buffer": buffer_info,
    }
