"""Tests for the bt_oximeter integration initialization."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bt_oximeter import async_setup_entry, async_unload_entry
from custom_components.bt_oximeter.const import DOMAIN, PLATFORMS


class TestBTOximeterInit:
    """Test bt_oximeter integration initialization."""

    @pytest.mark.asyncio
    async def test_setup_entry_no_address(self, hass: HomeAssistant) -> None:
        """Test setup fails when config entry has no address."""
        # Arrange - Config entry without address
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "name": "Test Oximeter",
                "model": "JKS50F",
                # Missing "address" key
            },
        )
        config_entry.add_to_hass(hass)

        # Act
        result = await async_setup_entry(hass, config_entry)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_setup_entry_unknown_model(self, hass: HomeAssistant) -> None:
        """Test setup fails when config entry has unknown device model."""
        # Arrange - Config entry with unknown model
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "address": "E0:4E:7A:21:5D:B0",
                "name": "Test Oximeter",
                "model": "UNKNOWN_MODEL_XYZ",
            },
        )
        config_entry.add_to_hass(hass)

        # Act
        result = await async_setup_entry(hass, config_entry)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_unload_entry(self, hass: HomeAssistant) -> None:
        """Test successful unload of a config entry."""
        # Arrange - First set up the entry
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "address": "E0:4E:7A:21:5D:B0",
                "name": "JKS-50F",
            },
        )
        config_entry.add_to_hass(hass)

        # Create a mock coordinator
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = mock_coordinator

        with patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_unload_platforms:
            # Act
            result = await async_unload_entry(hass, config_entry)

            # Assert
            assert result is True
            mock_unload_platforms.assert_called_once_with(config_entry, PLATFORMS)
            assert config_entry.entry_id not in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_entry_fails(self, hass: HomeAssistant) -> None:
        """Test unload fails when platform unload fails."""
        # Arrange
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "address": "E0:4E:7A:21:5D:B0",
                "name": "JKS-50F",
            },
        )
        config_entry.add_to_hass(hass)

        # Create a mock coordinator
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = mock_coordinator

        with patch(
            "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_unload_platforms:
            # Act
            result = await async_unload_entry(hass, config_entry)

            # Assert
            assert result is False
            mock_unload_platforms.assert_called_once_with(config_entry, PLATFORMS)
            # Coordinator should still be in hass.data since unload failed
            assert config_entry.entry_id in hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_multiple_entries(
        self, hass: HomeAssistant, mock_bleak_client
    ) -> None:
        """Test multiple config entries can coexist."""
        # Arrange
        entry1 = MockConfigEntry(
            domain=DOMAIN,
            data={
                "address": "E0:4E:7A:21:5D:B0",
                "name": "JKS-50F-1",
            },
        )
        entry1.add_to_hass(hass)

        entry2 = MockConfigEntry(
            domain=DOMAIN,
            data={
                "address": "E0:4E:7A:21:5D:B1",
                "name": "JKS-50F-2",
            },
        )
        entry2.add_to_hass(hass)

        with (
            patch(
                "custom_components.bt_oximeter.OximeterBluetoothCoordinator.async_config_entry_first_refresh",
                new_callable=AsyncMock,
            ),
            patch(
                "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
        ):
            # Act
            result1 = await async_setup_entry(hass, entry1)
            result2 = await async_setup_entry(hass, entry2)

            # Assert
            assert result1 is True
            assert result2 is True
            assert len(hass.data[DOMAIN]) == 2
            assert entry1.entry_id in hass.data[DOMAIN]
            assert entry2.entry_id in hass.data[DOMAIN]
