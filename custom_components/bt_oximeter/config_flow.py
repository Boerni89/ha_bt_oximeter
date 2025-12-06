from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers import selector

from .const import DEFAULT_NAME, DOMAIN, CONF_MODEL
from .devices import SUPPORTED_DEVICES

_LOGGER = logging.getLogger(__name__)


class OximeterBTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Bluetooth Oximeter."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None
        self._discovered_model: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ):
        """Triggered when the device is discovered via Bluetooth."""
        address = discovery_info.address
        name = discovery_info.name or DEFAULT_NAME

        # Validate this is actually a supported oximeter device
        # Check MAC address OUI against all supported device models
        mac_oui = address.upper().replace(":", "")[:6]

        # Collect all supported OUIs from all device models
        all_supported_ouis = []
        for device_class in SUPPORTED_DEVICES.values():
            device_instance = device_class()
            all_supported_ouis.extend(device_instance.device_info.supported_ouis)

        if mac_oui not in all_supported_ouis:
            _LOGGER.debug(
                "Ignoring device %s - unknown MAC OUI %s (not a supported oximeter model)",
                address,
                mac_oui,
            )
            return self.async_abort(reason="not_supported")

        # Check if already configured with this address
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        # Store discovery info for later use
        self._discovered_address = address
        self._discovered_name = name

        # Store data in context for later steps
        self.context["title_placeholders"] = {"name": name}

        # Show confirmation dialog asking user if they want to add this device
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": name, "address": address},
        )

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """User confirmed and can edit name/address of discovered device."""
        errors: dict[str, str] = {}

        if user_input is None:
            # Show form with pre-filled values from discovery
            return self.async_show_form(
                step_id="bluetooth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_NAME, default=self._discovered_name or DEFAULT_NAME
                        ): str,
                        vol.Required(
                            CONF_ADDRESS, default=self._discovered_address or ""
                        ): str,
                        vol.Required(
                            CONF_MODEL, default="JKS50F"
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=list(SUPPORTED_DEVICES.keys()),
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                    }
                ),
                description_placeholders={
                    "name": self._discovered_name or DEFAULT_NAME,
                    "address": self._discovered_address or "",
                },
            )

        # Extract and normalize input
        address = user_input[CONF_ADDRESS].strip().upper()
        name = user_input[CONF_NAME].strip() or DEFAULT_NAME
        model = user_input[CONF_MODEL]

        # Validate MAC address format
        if not self._is_valid_mac_address(address):
            errors["base"] = "invalid_mac_address"
            return self.async_show_form(
                step_id="bluetooth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default=name): str,
                        vol.Required(CONF_ADDRESS, default=address): str,
                    }
                ),
                errors=errors,
                description_placeholders={
                    "name": self._discovered_name or DEFAULT_NAME,
                    "address": self._discovered_address or "",
                },
            )

        # Set unique ID to MAC address to prevent duplicates
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        # Create the config entry
        return self.async_create_entry(
            title=name,
            data={
                CONF_ADDRESS: address,
                CONF_NAME: name,
                CONF_MODEL: model,
            },
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle manual setup or configuration after discovery."""
        errors: dict[str, str] = {}

        if user_input is None:
            # Show form with optional pre-filled values from discovery
            default_name = self._discovered_name or DEFAULT_NAME
            default_address = self._discovered_address or ""

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default=default_name): str,
                        vol.Required(CONF_ADDRESS, default=default_address): str,
                        vol.Required(
                            CONF_MODEL, default="JKS50F"
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=list(SUPPORTED_DEVICES.keys()),
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                    }
                ),
                errors=errors,
            )

        # Extract and normalize input
        address = user_input[CONF_ADDRESS].strip().upper()
        name = user_input[CONF_NAME].strip() or DEFAULT_NAME
        model = user_input[CONF_MODEL]

        # Validate MAC address format
        if not self._is_valid_mac_address(address):
            errors["base"] = "invalid_mac_address"
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME, default=name): str,
                        vol.Required(CONF_ADDRESS, default=address): str,
                    }
                ),
                errors=errors,
            )

        # Set unique ID to MAC address to prevent duplicates
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        # Create the config entry
        return self.async_create_entry(
            title=name,
            data={
                CONF_ADDRESS: address,
                CONF_NAME: name,
                CONF_MODEL: model,
            },
        )

    @staticmethod
    def _is_valid_mac_address(address: str) -> bool:
        """Validate MAC address format (XX:XX:XX:XX:XX:XX)."""
        parts = address.split(":")
        if len(parts) != 6:
            return False
        try:
            for part in parts:
                int(part, 16)
            return True
        except ValueError:
            return False
