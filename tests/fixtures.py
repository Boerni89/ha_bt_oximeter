"""Test configuration for Bluetooth Oximeter."""

from unittest.mock import AsyncMock, MagicMock, patch

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
import pytest

from custom_components.bt_oximeter.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    return


@pytest.fixture
def mock_bleak_scanner():
    """Mock BleakScanner."""
    with patch(
        "homeassistant.components.bluetooth.scanner.OriginalBleakScanner"
    ) as mock_scanner:
        yield mock_scanner


@pytest.fixture
def mock_bluetooth_adapters():
    """Mock Bluetooth adapters."""
    with (
        patch("homeassistant.components.bluetooth.HaBleakScannerWrapper"),
        patch("homeassistant.components.bluetooth.storage.BluetoothStorage"),
    ):
        yield


@pytest.fixture
def mock_bleak_client():
    """Mock BleakClient."""
    with patch(
        "custom_components.bt_oximeter.coordinator.BleakClientWithServiceCache"
    ) as mock_client_class:
        client = mock_client_class.return_value
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock()
        client.start_notify = AsyncMock()
        client.stop_notify = AsyncMock()
        client.disconnect = AsyncMock()
        client.is_connected = True

        # Mock BLE device
        ble_device = MagicMock(spec=BLEDevice)
        ble_device.address = "E0:4E:7A:21:5D:B0"
        ble_device.name = "OXIMETER"
        client.ble_device = ble_device

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
