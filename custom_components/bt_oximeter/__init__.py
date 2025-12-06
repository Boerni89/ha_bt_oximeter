from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, CONF_MODEL
from .coordinator import OximeterBluetoothCoordinator
from .devices import SUPPORTED_DEVICES

_LOGGER = logging.getLogger(__name__)

# Integration can only be set up via config entry (UI)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Bluetooth Oximeter component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Oximeter from a config entry."""
    # MAC address is stored in entry.data from config_flow
    address = entry.data.get("address")

    if not address:
        _LOGGER.error("No address found in config entry")
        return False

    # Get device model from config entry, default to JKS50F for backwards compatibility
    model = entry.data.get(CONF_MODEL, "JKS50F")

    # Get device class from registry
    device_class = SUPPORTED_DEVICES.get(model)
    if not device_class:
        _LOGGER.error("Unknown device model: %s", model)
        return False

    # Create device instance based on selected model
    device = device_class()

    coordinator = OximeterBluetoothCoordinator(
        hass=hass,
        logger=_LOGGER,
        address=address,
        device=device,
        config_entry=entry,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Try to establish initial connection, but don't fail if device is off
    # The coordinator will retry on the next update cycle
    await coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry and disconnect from device."""
    coordinator: OximeterBluetoothCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Disconnect from device
    await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
