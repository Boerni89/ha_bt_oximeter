"""Base classes for oximeter device implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class OximeterMeasurement:
    """Measurement data from an oximeter device."""

    finger_present: bool
    spo2: int | None  # Percentage, None = invalid
    pulse: int | None  # bpm, None = invalid
    perfusion_index: float | None  # Percentage, None = invalid
    timestamp: datetime


@dataclass
class DeviceInfo:
    """Device metadata for an oximeter model."""

    manufacturer: str
    model: str
    frame_header: bytes
    frame_length: int
    service_uuid: str
    notify_uuid: str
    supported_ouis: list[str]  # MAC address OUI prefixes (first 6 hex digits)


class OximeterDeviceBase(ABC):
    """Base class for oximeter device implementations."""

    def __init__(self) -> None:
        """Initialize device."""
        self.last_measurement: OximeterMeasurement | None = None
        self._buffer: bytearray = bytearray()

    @property
    @abstractmethod
    def device_info(self) -> DeviceInfo:
        """Return device metadata."""

    @abstractmethod
    def add_to_buffer(self, data: bytes) -> None:
        """Add incoming BLE notification data to internal buffer.

        Called from notification handler - should be fast.
        Implementation depends on device protocol.
        """

    @abstractmethod
    def extract_measurement(self) -> OximeterMeasurement | None:
        """Extract a measurement from buffered data if available.

        Called periodically by coordinator.
        Returns None if no complete measurement is available yet.
        """

    def get_buffer_info(self) -> dict[str, Any]:
        """Return buffer information for diagnostics."""
        return {
            "size": len(self._buffer),
            "content_hex": self._buffer.hex() if self._buffer else "",
            "max_size": 2 * self.device_info.frame_length,
        }
