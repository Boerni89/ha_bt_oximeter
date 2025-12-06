"""Test the Bluetooth Oximeter config flow."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.bt_oximeter.const import DOMAIN


class TestBTOximeterConfigFlow:
    """Test BTOximeterConfigFlow class."""

    @pytest.mark.asyncio
    async def test_bluetooth_discovery(
        self, hass: HomeAssistant, jks50f_service_info, mock_bleak_client
    ) -> None:
        """Test discovery via bluetooth with JKS50F device."""
        # Act
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=jks50f_service_info,
        )

        # Assert
        pytest.helpers.assert_flow_form_shown(result, "bluetooth_confirm")
        assert "description_placeholders" in result
        assert result["description_placeholders"]["name"] == "OXIMETER"

    @pytest.mark.asyncio
    async def test_bluetooth_discovery_unsupported(
        self, hass: HomeAssistant, unsupported_service_info
    ) -> None:
        """Test discovery aborts for unsupported devices."""
        # Act
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=unsupported_service_info,
        )

        # Assert
        pytest.helpers.assert_flow_aborted(result, "not_supported")

    @pytest.mark.asyncio
    async def test_user_flow(self, hass: HomeAssistant, mock_bleak_client) -> None:
        """Test user initiated flow shows form."""
        # Act
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )

        # Assert
        pytest.helpers.assert_flow_form_shown(result, "user")

    @pytest.mark.asyncio
    async def test_bluetooth_confirm_creates_entry(
        self, hass: HomeAssistant, jks50f_service_info, mock_bleak_client
    ) -> None:
        """Test bluetooth confirm step creates config entry."""
        # Arrange
        with patch(
            "custom_components.bt_oximeter.async_setup_entry", return_value=True
        ):
            _result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_BLUETOOTH},
                data=jks50f_service_info,
            )

            pytest.helpers.assert_flow_form_shown(_result, "bluetooth_confirm")

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

    @pytest.mark.asyncio
    async def test_bluetooth_confirm_shows_form(
        self, hass: HomeAssistant, jks50f_service_info
    ) -> None:
        """Test bluetooth confirm shows form when called without user_input."""
        # Arrange - Start the flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=jks50f_service_info,
        )
        assert result["type"] == FlowResultType.FORM
        flow_id = result["flow_id"]

        # Get the flow instance to call the method directly
        flow = hass.config_entries.flow._progress[flow_id]

        # Act - Call async_step_bluetooth_confirm with user_input=None
        result = await flow.async_step_bluetooth_confirm(user_input=None)

        # Assert - Should show form with pre-filled values
        pytest.helpers.assert_flow_form_shown(result, "bluetooth_confirm")
        assert "description_placeholders" in result

    @pytest.mark.asyncio
    async def test_bluetooth_confirm_invalid_mac(
        self, hass: HomeAssistant, jks50f_service_info
    ) -> None:
        """Test bluetooth confirm with invalid MAC address."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_BLUETOOTH},
            data=jks50f_service_info,
        )
        pytest.helpers.assert_flow_form_shown(result, "bluetooth_confirm")

        # Try to confirm with invalid MAC
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "My Oximeter",
                CONF_ADDRESS: "invalid-mac",
                CONF_MODEL: "JKS50F",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "bluetooth_confirm"
        assert result["errors"] == {"base": "invalid_mac_address"}

    @pytest.mark.asyncio
    async def test_user_flow_invalid_mac(self, hass: HomeAssistant) -> None:
        """Test user flow with invalid MAC address."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        pytest.helpers.assert_flow_form_shown(result, "user")

        # Try to submit with invalid MAC
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Test Oximeter",
                CONF_ADDRESS: "not-a-mac",
                CONF_MODEL: "JKS50F",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "invalid_mac_address"}

    @pytest.mark.asyncio
    async def test_user_flow_duplicate_entry(
        self, hass: HomeAssistant, mock_config_entry
    ) -> None:
        """Test user flow aborts if device already configured."""
        # Add existing config entry
        mock_config_entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        pytest.helpers.assert_flow_form_shown(result, "user")

        # Try to add same device
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Another Name",
                CONF_ADDRESS: "E0:4E:7A:21:5D:B0",  # Same as mock_config_entry
                CONF_MODEL: "JKS50F",
            },
        )

        pytest.helpers.assert_flow_aborted(result, "already_configured")

    @pytest.mark.asyncio
    async def test_user_flow_successful_creation(self, hass: HomeAssistant) -> None:
        """Test successful user flow creates entry."""
        # Arrange
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        pytest.helpers.assert_flow_form_shown(result, "user")

        # Act - Submit valid data
        with patch(
            "custom_components.bt_oximeter.async_setup_entry", return_value=True
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_NAME: "My Oximeter",
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    CONF_MODEL: "JKS50F",
                },
            )

        # Assert - Entry created successfully
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "My Oximeter"
        assert result["data"][CONF_ADDRESS] == "AA:BB:CC:DD:EE:FF"
        assert result["data"][CONF_MODEL] == "JKS50F"

    def test_is_valid_mac_address_with_non_hex_chars(self) -> None:
        """Test _is_valid_mac_address ValueError handling."""
        # Arrange - Import the config flow to access static method
        from custom_components.bt_oximeter.config_flow import OximeterBTConfigFlow

        # Act & Assert - Invalid hex characters trigger ValueError
        assert OximeterBTConfigFlow._is_valid_mac_address("ZZ:XX:YY:GG:HH:II") is False
        assert OximeterBTConfigFlow._is_valid_mac_address("00:11:22:33:44:ZZ") is False

        # Valid MAC should still work
        assert OximeterBTConfigFlow._is_valid_mac_address("AA:BB:CC:DD:EE:FF") is True
