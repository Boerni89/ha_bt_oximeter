from __future__ import annotations

import asyncio
import logging
from datetime import timedelta, datetime
from typing import TYPE_CHECKING, Any

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

from .const import UPDATE_INTERVAL
from .device_base import OximeterDeviceBase, OximeterMeasurement

_LOGGER = logging.getLogger(__name__)


class OximeterBluetoothCoordinator(DataUpdateCoordinator[OximeterMeasurement]):
    """Coordinator that maintains a persistent BLE connection with continuous notifications."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        address: str,
        device: OximeterDeviceBase,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=logger,
            name="Pulse Oximeter",
            update_interval=UPDATE_INTERVAL,
            config_entry=config_entry,
        )
        self.address = address
        self.device = device
        self._client: BleakClientWithServiceCache | None = None
        self._connect_lock = asyncio.Lock()
        self._available = False  # Track device availability
        self._unavailable_logged = False  # Track if we already logged unavailability

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self._available

    def get_connection_info(self) -> dict[str, Any]:
        """Return BLE connection information for diagnostics."""
        return {
            "is_connected": self._client.is_connected if self._client else False,
            "client_exists": self._client is not None,
        }

    async def _async_refresh(
        self,
        log_failures: bool = True,
        raise_on_auth_failed: bool = False,
        scheduled: bool = False,
        raise_on_entry_error: bool = False,
    ) -> None:
        """Refresh data and suppress error logging for battery devices."""
        try:
            await super()._async_refresh(
                log_failures=False,  # We handle our own logging
                raise_on_auth_failed=raise_on_auth_failed,
                scheduled=scheduled,
                raise_on_entry_error=raise_on_entry_error,
            )
        except UpdateFailed:
            # Suppress the exception - device being off is normal for battery devices
            # Our custom logging in _ensure_connected() already handles this
            pass

    async def _ensure_connected(self) -> None:
        """Ensure we have an active BLE connection."""
        if self._client and self._client.is_connected:
            return

        async with self._connect_lock:
            # Check again after acquiring lock
            if self._client and self._client.is_connected:
                return

            _LOGGER.debug("Establishing connection to Oximeter %s", self.address)

            # Get fresh BLE device info
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if not ble_device:
                raise UpdateFailed(f"Device {self.address} not found")

            try:
                # Use shorter timeout: 2 attempts with 5s timeout each = max 10s total
                self._client = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    ble_device.name or "Pulse Oximeter",
                    max_attempts=2,  # Reduced from default 4
                    timeout=5.0,  # 5 seconds per attempt instead of default 20s
                )

                # Start notifications
                await self._client.start_notify(
                    self.device.device_info.notify_uuid, self._notification_handler
                )

                # Log reconnection if was previously unavailable
                if self._unavailable_logged:
                    _LOGGER.info("Oximeter %s is back online", self.address)
                    self._unavailable_logged = False
                else:
                    _LOGGER.info(
                        "Connected to Oximeter %s, notifications started", self.address
                    )

                self._available = True  # Mark as available after successful connection

            except BleakError as ex:
                self._client = None
                self._available = False

                # Log only once when device becomes unavailable (battery devices are often off)
                if not self._unavailable_logged:
                    _LOGGER.info(
                        "Oximeter %s is unavailable (device may be turned off)",
                        self.address,
                    )
                    self._unavailable_logged = True

                raise UpdateFailed(f"Device unavailable: {ex}") from ex

    def _notification_handler(self, sender: Any, data: bytearray) -> None:
        """Handle incoming BLE notifications - buffer data only."""
        # _LOGGER.debug("Received %d bytes via notification", len(data))
        self.device.add_to_buffer(data)

    async def _async_update_data(self) -> OximeterMeasurement:
        """Fetch data by extracting from the notification buffer."""
        # Ensure we have a connection
        await self._ensure_connected()

        # Extract measurement from buffered notification data
        measurement = self.device.extract_measurement()

        if measurement is not None:
            # Update our stored data
            _LOGGER.debug(
                "Oximeter data: SpO2=%s%%, Pulse=%s bpm, PI=%s%%, Finger=%s",
                measurement.spo2,
                measurement.pulse,
                measurement.perfusion_index,
                measurement.finger_present,
            )
            return measurement

        # No complete frame yet
        if self.data is not None:
            # Return last known data to keep connection alive
            _LOGGER.debug("No new frame yet, returning cached data")
            return self.data

        # First call and no data yet - return empty measurement
        # This keeps the connection open while waiting for first notification
        _LOGGER.debug("Waiting for first measurement from notifications")

        return OximeterMeasurement(
            finger_present=False,
            spo2=None,
            pulse=None,
            perfusion_index=None,
            timestamp=datetime.now(),
        )

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and disconnect."""
        if self._client and self._client.is_connected:
            try:
                await self._client.stop_notify(self.device.device_info.notify_uuid)
            except Exception:
                pass
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
            self._available = False
            _LOGGER.info("Disconnected from Oximeter %s", self.address)
