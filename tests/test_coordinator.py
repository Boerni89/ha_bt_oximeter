"""Test coordinator functionality."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.bt_oximeter.coordinator import OximeterBluetoothCoordinator
from custom_components.bt_oximeter.device_base import OximeterMeasurement


class TestOximeterCoordinator:
    """Test OximeterBluetoothCoordinator class."""

    @pytest.mark.asyncio
    async def test_coordinator_initialization(
        self, hass, mock_device, mock_config_entry
    ) -> None:
        """Test coordinator can be initialized."""
        # Arrange & Act
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        # Assert
        assert coordinator.address == "E0:4E:7A:21:5D:B0"
        assert coordinator.device == mock_device
        assert coordinator.name == "Pulse Oximeter"
        assert not coordinator.available  # Not connected yet

    @pytest.mark.asyncio
    async def test_coordinator_update_success(
        self, hass, mock_device, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test successful data update from coordinator."""
        # Arrange
        mock_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        # Coordinator calls extract_measurement, not get_measurement
        mock_device.extract_measurement.return_value = mock_measurement

        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        # Act
        await coordinator.async_refresh()

        # Assert
        assert coordinator.data == mock_measurement
        assert coordinator.data.spo2 == 98
        assert coordinator.data.pulse == 72
        assert coordinator.available

    @pytest.mark.asyncio
    async def test_coordinator_handles_disconnection(
        self, hass, mock_device, mock_config_entry
    ) -> None:
        """Test coordinator handles device disconnection gracefully."""
        # Arrange
        from homeassistant.helpers.update_coordinator import UpdateFailed

        # Mock bluetooth device as not found
        with patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_device:
            mock_ble_device.return_value = None

            coordinator = OximeterBluetoothCoordinator(
                hass=hass,
                logger=MagicMock(),
                address="E0:4E:7A:21:5D:B0",
                device=mock_device,
                config_entry=mock_config_entry,
            )

            # Act - async_refresh() catches UpdateFailed internally for battery devices
            await coordinator.async_refresh()

            # Assert - coordinator should still be unavailable
            assert not coordinator.available
            assert coordinator.data is None

    @pytest.mark.asyncio
    async def test_coordinator_returns_cached_data_when_no_new_frame(
        self, hass, mock_device, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test coordinator returns cached data when no new measurement available."""
        # Arrange
        initial_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )

        # First call returns data, second call returns None (no new frame)
        mock_device.extract_measurement.side_effect = [initial_measurement, None]

        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        # Act - first refresh gets data
        await coordinator.async_refresh()
        assert coordinator.data == initial_measurement

        # Second refresh gets no new frame, should return cached data
        await coordinator.async_refresh()

        # Assert - still has cached data
        assert coordinator.data == initial_measurement
        assert coordinator.data.spo2 == 98

    @pytest.mark.asyncio
    async def test_coordinator_returns_empty_measurement_on_first_call(
        self, hass, mock_device, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test coordinator returns empty measurement when no data yet."""
        # Arrange
        mock_device.extract_measurement.return_value = None

        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        # Act
        await coordinator.async_refresh()

        # Assert - returns empty measurement
        assert coordinator.data is not None
        assert coordinator.data.finger_present is False
        assert coordinator.data.spo2 is None
        assert coordinator.data.pulse is None

    @pytest.mark.asyncio
    async def test_notification_handler_adds_data_to_buffer(
        self, hass, mock_device, mock_config_entry
    ) -> None:
        """Test notification handler buffers incoming BLE data."""
        # Arrange
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        test_data = bytearray(b"\xff\x44\x01\x00\x64\x50")

        # Act
        coordinator._notification_handler(None, test_data)

        # Assert
        mock_device.add_to_buffer.assert_called_once_with(test_data)

    @pytest.mark.asyncio
    async def test_coordinator_reconnection_logging(
        self, hass, mock_device, mock_config_entry, mock_bleak_client, caplog
    ) -> None:
        """Test coordinator logs reconnection after being unavailable."""
        import logging

        from bleak.exc import BleakError

        # Arrange
        caplog.set_level(logging.INFO)
        mock_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_device.extract_measurement.return_value = mock_measurement

        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        # First connection succeeds
        await coordinator.async_refresh()
        assert "notifications started" in caplog.text
        caplog.clear()

        # Simulate disconnection
        mock_bleak_client.is_connected = False

        # Mock BleakError on next connection attempt
        with patch(
            "custom_components.bt_oximeter.coordinator.establish_connection",
            side_effect=BleakError("Connection failed"),
        ):
            await coordinator.async_refresh()
            assert "is unavailable" in caplog.text
            assert coordinator._unavailable_logged is True
            caplog.clear()

        # Reconnection succeeds
        mock_bleak_client.is_connected = True
        await coordinator.async_refresh()

        # Assert - should log "back online"
        assert "back online" in caplog.text

    @pytest.mark.asyncio
    async def test_async_shutdown_disconnects_client(
        self, hass, mock_device, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test async_shutdown properly disconnects BLE client."""
        # Arrange
        mock_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_device.extract_measurement.return_value = mock_measurement

        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=mock_device,
            config_entry=mock_config_entry,
        )

        # Connect first
        await coordinator.async_refresh()
        assert coordinator.available

        # Act
        await coordinator.async_shutdown()

        # Assert
        mock_bleak_client.stop_notify.assert_called_once()
        mock_bleak_client.disconnect.assert_called_once()
        assert not coordinator.available
        assert coordinator._client is None
