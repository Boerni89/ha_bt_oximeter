"""Test diagnostics for Bluetooth Oximeter."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from custom_components.bt_oximeter.coordinator import OximeterBluetoothCoordinator
from custom_components.bt_oximeter.device_base import OximeterMeasurement
from custom_components.bt_oximeter.devices.jks50f import JKS50FDevice
from custom_components.bt_oximeter.diagnostics import async_get_config_entry_diagnostics


class TestDiagnostics:
    """Test diagnostics functionality."""

    @pytest.mark.asyncio
    async def test_diagnostics_returns_redacted_data(
        self, hass, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test diagnostics returns data with redacted sensitive info."""
        # Arrange
        device = JKS50FDevice()
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=device,
            config_entry=mock_config_entry,
        )

        mock_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        coordinator.data = mock_measurement
        hass.data["bt_oximeter"] = {mock_config_entry.entry_id: coordinator}

        # Act
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Assert
        assert "entry" in diagnostics
        assert diagnostics["entry"]["data"]["address"] == "**REDACTED**"
        assert "device" in diagnostics
        assert "coordinator" in diagnostics
        assert diagnostics["current_measurement"]["spo2"] == 98
        assert "buffer" in diagnostics
        assert diagnostics["buffer"]["size"] == 0  # Empty buffer initially
        assert "connection" in diagnostics
        assert "last_measurement" in diagnostics
        assert diagnostics["last_measurement"] is None  # No last measurement yet
        assert "bluetooth_device" in diagnostics

    @pytest.mark.asyncio
    async def test_diagnostics_with_buffer_data(
        self, hass, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test diagnostics includes buffer information."""
        # Arrange
        device = JKS50FDevice()
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=device,
            config_entry=mock_config_entry,
        )

        # Add some data to the buffer
        test_data = b"\xff\x44\x01\x02\x03\x04"
        device.add_to_buffer(test_data)

        # Don't set coordinator.data - it will be None by default
        hass.data["bt_oximeter"] = {mock_config_entry.entry_id: coordinator}

        # Act
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Assert
        assert "buffer" in diagnostics
        assert diagnostics["buffer"]["size"] == len(test_data)
        assert diagnostics["buffer"]["content_hex"] == test_data.hex()
        assert diagnostics["buffer"]["max_size"] == 2 * device.device_info.frame_length
        assert "connection" in diagnostics
        assert diagnostics["connection"]["client_exists"] is False
        assert diagnostics["connection"]["is_connected"] is False

    @pytest.mark.asyncio
    async def test_diagnostics_with_last_measurement(
        self, hass, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test diagnostics includes last measurement when available."""
        # Arrange
        device = JKS50FDevice()
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=device,
            config_entry=mock_config_entry,
        )

        # Set a last measurement on the device
        last_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=95,
            pulse=68,
            perfusion_index=4.8,
            timestamp=datetime(2024, 1, 1, 11, 0, 0),
        )
        device.last_measurement = last_measurement

        # Current measurement is different
        current_measurement = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )
        coordinator.data = current_measurement

        hass.data["bt_oximeter"] = {mock_config_entry.entry_id: coordinator}

        # Act
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Assert
        assert "last_measurement" in diagnostics
        assert diagnostics["last_measurement"] is not None
        assert diagnostics["last_measurement"]["spo2"] == 95
        assert diagnostics["last_measurement"]["pulse"] == 68
        assert diagnostics["last_measurement"]["perfusion_index"] == 4.8
        assert diagnostics["last_measurement"]["timestamp"] == "2024-01-01T11:00:00"

        # Current should be different
        assert diagnostics["current_measurement"]["spo2"] == 98
        assert diagnostics["current_measurement"]["pulse"] == 72

    @pytest.mark.asyncio
    async def test_diagnostics_connection_info(
        self, hass, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test diagnostics includes connection information."""
        # Arrange
        device = JKS50FDevice()
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=device,
            config_entry=mock_config_entry,
        )

        hass.data["bt_oximeter"] = {mock_config_entry.entry_id: coordinator}

        # Act
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Assert - connection info should exist
        assert "connection" in diagnostics
        assert isinstance(diagnostics["connection"], dict)
        assert "is_connected" in diagnostics["connection"]
        assert "client_exists" in diagnostics["connection"]
        # Without a real connection, both should be False
        assert diagnostics["connection"]["is_connected"] is False
        assert diagnostics["connection"]["client_exists"] is False

    @pytest.mark.asyncio
    async def test_diagnostics_bluetooth_device_info(
        self, hass, mock_config_entry, mock_bleak_client
    ) -> None:
        """Test diagnostics includes bluetooth device information."""
        # Arrange
        device = JKS50FDevice()
        coordinator = OximeterBluetoothCoordinator(
            hass=hass,
            logger=MagicMock(),
            address="E0:4E:7A:21:5D:B0",
            device=device,
            config_entry=mock_config_entry,
        )

        hass.data["bt_oximeter"] = {mock_config_entry.entry_id: coordinator}

        # Act
        diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

        # Assert - bluetooth_device info should exist (may be None if device not found)
        assert "bluetooth_device" in diagnostics
        # The actual content depends on whether a BLE device is available in tests
