"""Test bt_oximeter sensor entities."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.bt_oximeter.const import DOMAIN
from custom_components.bt_oximeter.device_base import OximeterMeasurement
from custom_components.bt_oximeter.sensor import (
    SENSORS,
    OximeterSensorEntity,
    async_setup_entry,
)


class TestOximeterSensorEntityEntities:
    """Test oximeter sensor entities."""

    @pytest.mark.asyncio
    async def test_sensor_platform_setup(
        self, hass: HomeAssistant, mock_device, mock_config_entry
    ) -> None:
        """Test sensor platform setup."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=75,
            perfusion_index=5.5,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = mock_device
        mock_coordinator.last_update_success = True
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"

        # Setup hass.data correctly
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

        added_entities = []

        def mock_async_add_entities(entities, update_before_add=True):
            added_entities.extend(entities)

        # Act
        await async_setup_entry(hass, mock_config_entry, mock_async_add_entities)

        # Assert
        assert len(added_entities) == len(SENSORS)
        assert all(
            isinstance(entity, OximeterSensorEntity) for entity in added_entities
        )

    @pytest.mark.asyncio
    async def test_spo2_sensor_state(self, hass: HomeAssistant, mock_device) -> None:
        """Test SpO2 sensor state and attributes."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = mock_device
        mock_coordinator.last_update_success = True
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = True

        # Find SpO2 sensor description
        spo2_description = next(desc for desc in SENSORS if desc.key == "spo2")

        # Create sensor entity
        sensor = OximeterSensorEntity(mock_coordinator, "test_entry", spo2_description)

        # Act
        native_value = sensor.native_value

        # Assert
        assert native_value == 98
        assert sensor.native_unit_of_measurement == PERCENTAGE
        assert sensor.available

    @pytest.mark.asyncio
    async def test_pulse_rate_sensor_state(
        self, hass: HomeAssistant, mock_device
    ) -> None:
        """Test pulse rate sensor state and attributes."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = mock_device
        mock_coordinator.last_update_success = True
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = True

        # Find pulse rate sensor description
        pulse_description = next(desc for desc in SENSORS if desc.key == "pulse_rate")

        # Create sensor entity
        sensor = OximeterSensorEntity(mock_coordinator, "test_entry", pulse_description)

        # Act
        native_value = sensor.native_value

        # Assert
        assert native_value == 72
        assert sensor.native_unit_of_measurement == "bpm"
        assert sensor.available

    @pytest.mark.asyncio
    async def test_perfusion_index_sensor_state(
        self, hass: HomeAssistant, mock_device
    ) -> None:
        """Test perfusion index sensor state and attributes."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = mock_device
        mock_coordinator.last_update_success = True
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = True

        # Find perfusion index sensor description
        pi_description = next(desc for desc in SENSORS if desc.key == "perfusion_index")

        # Create sensor entity
        sensor = OximeterSensorEntity(mock_coordinator, "test_entry", pi_description)

        # Act
        native_value = sensor.native_value

        # Assert
        assert native_value == 5.2
        assert sensor.native_unit_of_measurement == PERCENTAGE
        assert sensor.available

    @pytest.mark.asyncio
    async def test_sensor_unavailable_when_no_data(
        self, hass: HomeAssistant, mock_device
    ) -> None:
        """Test sensor becomes unavailable when coordinator has no data."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = None
        mock_coordinator.device = mock_device
        mock_coordinator.last_update_success = True
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = False

        spo2_description = next(desc for desc in SENSORS if desc.key == "spo2")
        sensor = OximeterSensorEntity(mock_coordinator, "test_entry", spo2_description)
        spo2_description = next(desc for desc in SENSORS if desc.key == "spo2")

        # Act & Assert
        assert not sensor.available
        assert sensor.native_value is None

    @pytest.mark.asyncio
    async def test_sensor_none_value_handling(
        self, hass: HomeAssistant, mock_device
    ) -> None:
        """Test sensor handles None values in measurement data."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=None,  # No finger detected yet
            pulse=None,
            perfusion_index=None,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = mock_device
        mock_coordinator.last_update_success = True
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = True

        spo2_description = next(desc for desc in SENSORS if desc.key == "spo2")
        sensor = OximeterSensorEntity(mock_coordinator, "test_entry", spo2_description)

        # Act
        native_value = sensor.native_value

        # Assert
        assert native_value is None
        assert sensor.available  # Still available, just no reading
