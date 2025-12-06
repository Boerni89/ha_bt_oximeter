"""Test bt_oximeter binary sensor entities."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.bt_oximeter.binary_sensor import (
    BINARY_SENSORS,
    OximeterFingerEntity,
    async_setup_entry,
)
from custom_components.bt_oximeter.const import DOMAIN
from custom_components.bt_oximeter.device_base import OximeterMeasurement


class TestOximeterBinarySensorEntities:
    """Test oximeter binary sensor entities."""

    @pytest.mark.asyncio
    async def test_binary_sensor_platform_setup(
        self, hass: HomeAssistant, mock_device, mock_config_entry
    ) -> None:
        """Test binary sensor platform setup."""
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
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"

        # Setup hass.data correctly
        hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

        added_entities = []

        def mock_async_add_entities(new_entities, update_before_add=True):
            added_entities.extend(new_entities)

        # Act
        await async_setup_entry(hass, mock_config_entry, mock_async_add_entities)

        # Assert
        assert len(added_entities) == len(BINARY_SENSORS)
        assert all(
            isinstance(entity, OximeterFingerEntity) for entity in added_entities
        )

    @pytest.mark.asyncio
    async def test_finger_entity_is_on_when_present(self, hass: HomeAssistant) -> None:
        """Test finger detection binary sensor reports on when finger is present."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = MagicMock()
        mock_coordinator.device.device_info = MagicMock()
        mock_coordinator.device.device_info.manufacturer = "Test"
        mock_coordinator.device.device_info.model = "JKS50F"
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = True

        description = BinarySensorEntityDescription(
            key="finger",
            icon="mdi:hand-back-right",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        )

        # Create binary sensor entity
        sensor = OximeterFingerEntity(mock_coordinator, "test_entry", description)

        # Act & Assert
        assert sensor.is_on is True
        assert sensor.available
        assert sensor.device_class == BinarySensorDeviceClass.CONNECTIVITY

    @pytest.mark.asyncio
    async def test_finger_entity_is_off_when_not_present(
        self, hass: HomeAssistant
    ) -> None:
        """Test finger detection binary sensor reports off when no finger."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=False,
            spo2=None,
            pulse=None,
            perfusion_index=None,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = MagicMock()
        mock_coordinator.device.device_info = MagicMock()
        mock_coordinator.device.device_info.manufacturer = "Test"
        mock_coordinator.device.device_info.model = "JKS50F"
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = True

        description = BinarySensorEntityDescription(
            key="finger",
            icon="mdi:hand-back-right",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        )

        # Create binary sensor entity
        sensor = OximeterFingerEntity(mock_coordinator, "test_entry", description)

        # Act & Assert
        assert sensor.is_on is False
        assert sensor.available

    @pytest.mark.asyncio
    async def test_finger_entity_unavailable_when_no_data(
        self, hass: HomeAssistant
    ) -> None:
        """Test binary sensor becomes unavailable when coordinator has no data."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = None
        mock_coordinator.device = MagicMock()
        mock_coordinator.device.device_info = MagicMock()
        mock_coordinator.device.device_info.manufacturer = "Test"
        mock_coordinator.device.device_info.model = "JKS50F"
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"
        mock_coordinator.last_update_success = False

        description = BinarySensorEntityDescription(
            key="finger",
            icon="mdi:hand-back-right",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        )

        # Create binary sensor entity
        sensor = OximeterFingerEntity(mock_coordinator, "test_entry", description)

        # Act & Assert
        assert not sensor.available
        assert sensor.is_on is None

    @pytest.mark.asyncio
    async def test_finger_entity_icon(self, hass: HomeAssistant) -> None:
        """Test finger detection binary sensor icon."""
        # Arrange
        mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
        mock_coordinator.data = OximeterMeasurement(
            finger_present=True,
            spo2=98,
            pulse=72,
            perfusion_index=5.2,
            timestamp=datetime.now(),
        )
        mock_coordinator.device = MagicMock()
        mock_coordinator.device.device_info = MagicMock()
        mock_coordinator.device.device_info.manufacturer = "Test"
        mock_coordinator.device.device_info.model = "JKS50F"
        mock_coordinator.address = "E0:4E:7A:21:5D:B0"

        description = BinarySensorEntityDescription(
            key="finger",
            icon="mdi:hand-back-right",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        )

        # Create binary sensor entity
        sensor = OximeterFingerEntity(mock_coordinator, "test_entry", description)

        # Act & Assert
        assert sensor.icon == "mdi:hand-back-right"
