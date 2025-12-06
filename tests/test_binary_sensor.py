"""Test Bluetooth Oximeter binary sensors."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.bt_oximeter.const import DOMAIN


class TestBTOximeterBinarySensor:
    """Test BTOximeterBinarySensor platform."""

    @pytest.mark.asyncio
    async def test_binary_sensor_platform_setup(
        self, hass: HomeAssistant, jks50f_service_info, mock_bleak_client
    ) -> None:
        """Test binary sensor platform can be set up via config flow."""
        # Arrange
        with patch(
            "custom_components.bt_oximeter.async_setup_entry", return_value=True
        ):
            _result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_BLUETOOTH},
                data=jks50f_service_info,
            )

            # Act
            result = await hass.config_entries.flow.async_configure(
                _result["flow_id"],
                user_input={
                    "address": "E0:4E:7A:21:5D:B0",
                    "name": "OXIMETER",
                    "model": "JKS50F",
                },
            )

        # Assert
        pytest.helpers.assert_config_entry_created(result, "OXIMETER")
