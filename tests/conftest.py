"""Configuration for pytest."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResultType

from custom_components.bt_oximeter.const import DOMAIN
from custom_components.bt_oximeter.device_base import OximeterMeasurement

# Add custom_components to Python path
CUSTOM_COMPONENTS_PATH = Path(__file__).parents[1].parent
sys.path.insert(0, str(CUSTOM_COMPONENTS_PATH))

# Enable pytest-homeassistant-custom-component
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations."""
    return


@pytest.fixture
def mock_bleak_client():
    """Mock BleakClient."""
    with (
        patch(
            "custom_components.bt_oximeter.coordinator.BleakClientWithServiceCache"
        ) as mock_client_class,
        patch(
            "custom_components.bt_oximeter.coordinator.establish_connection"
        ) as mock_establish,
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address"
        ) as mock_ble_addr,
    ):
        # Mock the BLE device
        ble_device = MagicMock(spec=BLEDevice)
        ble_device.address = "E0:4E:7A:21:5D:B0"
        ble_device.name = "OXIMETER"
        mock_ble_addr.return_value = ble_device

        # Mock the client instance
        client = MagicMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock()
        client.start_notify = AsyncMock()
        client.stop_notify = AsyncMock()
        client.disconnect = AsyncMock()
        client.is_connected = True
        client.ble_device = ble_device

        # Mock establish_connection to return our mocked client
        mock_establish.return_value = client
        mock_client_class.return_value = client

        yield client


@pytest.fixture
def jks50f_service_info():
    """Return JKS50F Bluetooth service info."""
    return BluetoothServiceInfoBleak(
        name="OXIMETER",
        address="E0:4E:7A:21:5D:B0",
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=["0000ffe0-0000-1000-8000-00805f9b34fb"],
        source="local",
        device=BLEDevice(
            address="E0:4E:7A:21:5D:B0",
            name="OXIMETER",
            details={},
        ),
        advertisement=AdvertisementData(
            local_name="OXIMETER",
            manufacturer_data={},
            service_data={},
            service_uuids=["0000ffe0-0000-1000-8000-00805f9b34fb"],
            tx_power=None,
            rssi=-60,
            platform_data=(),
        ),
        connectable=True,
        time=0,
        tx_power=None,
    )


@pytest.fixture
def mock_device():
    """Mock oximeter device."""
    device = MagicMock()
    device.name = "JKS50F"
    device.get_measurement.return_value = OximeterMeasurement(
        finger_present=True,
        spo2=98,
        pulse=72,
        perfusion_index=5.2,
        timestamp=datetime.now(),
    )
    return device


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "address": "E0:4E:7A:21:5D:B0",
            "name": "OXIMETER",
            "model": "JKS50F",
        },
        unique_id="E0:4E:7A:21:5D:B0",
    )


@pytest.fixture
def unsupported_service_info():
    """Return unsupported device Bluetooth service info."""
    return BluetoothServiceInfoBleak(
        name="RANDOM_DEVICE",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-70,
        manufacturer_data={},
        service_data={},
        service_uuids=["0000ffe0-0000-1000-8000-00805f9b34fb"],
        source="local",
        device=BLEDevice(
            address="AA:BB:CC:DD:EE:FF",
            name="RANDOM_DEVICE",
            details={},
        ),
        advertisement=AdvertisementData(
            local_name="RANDOM_DEVICE",
            manufacturer_data={},
            service_data={},
            service_uuids=["0000ffe0-0000-1000-8000-00805f9b34fb"],
            tx_power=None,
            rssi=-70,
            platform_data=(),
        ),
        connectable=True,
        time=0,
        tx_power=None,
    )


# Custom pytest helpers for bt_oximeter
@pytest.helpers.register
def assert_config_entry_created(result, expected_title_contains: str) -> None:
    """Assert that a config entry was created successfully.

    :param result: The flow result to check
    :type result: dict
    :param expected_title_contains: String that should be in the title
    :type expected_title_contains: str
    """
    assert result is not None
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert expected_title_contains in result["title"]


@pytest.helpers.register
def assert_flow_form_shown(result, expected_step_id: str) -> None:
    """Assert that a config flow form is shown.

    :param result: The flow result to check
    :type result: dict
    :param expected_step_id: Expected step ID
    :type expected_step_id: str
    """
    assert result is not None
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == expected_step_id


@pytest.helpers.register
def assert_flow_aborted(result, expected_reason: str) -> None:
    """Assert that a config flow was aborted.

    :param result: The flow result to check
    :type result: dict
    :param expected_reason: Expected abort reason
    :type expected_reason: str
    """
    assert result is not None
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == expected_reason
