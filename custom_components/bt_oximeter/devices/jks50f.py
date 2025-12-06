"""JKS50F Pulse Oximeter device implementation."""

from __future__ import annotations

import logging
from datetime import datetime

from ..device_base import DeviceInfo, OximeterDeviceBase, OximeterMeasurement

_LOGGER = logging.getLogger(__name__)


class JKS50FDevice(OximeterDeviceBase):
    """Implementation for JKS50F pulse oximeter."""

    def __init__(self) -> None:
        """Initialize JKS50F device."""
        super().__init__()

    @property
    def device_info(self) -> DeviceInfo:
        """Return JKS50F device metadata."""
        return DeviceInfo(
            manufacturer="Guangdong Health Medical Technology Co., Ltd.",
            model="JKS50F",
            frame_header=b"\xff\x44\x01",
            frame_length=69,
            service_uuid="0000ffe0-0000-1000-8000-00805f9b34fb",
            notify_uuid="0000ffe1-0000-1000-8000-00805f9b34fb",
            supported_ouis=[
                # All registered OUIs for Nanjing Qinheng Microelectronics Co., Ltd.
                # Source: IEEE OUI database (https://standards-oui.ieee.org/)
                "DC045A",
                "5414A7",
                "E04E7A",  # Confirmed oximeter
                "0C3D5E",
                "701988",
                "C817F5",
                "50547B",
                "5C5310",
            ],
        )

    def add_to_buffer(self, data: bytes) -> None:
        """Add new data to buffer and trim to max size.

        This is called from the notification handler and should be FAST.
        No parsing/decoding happens here - just buffer management.
        """
        self._buffer.extend(data)
        max_size = 2 * self.device_info.frame_length

        # Keep buffer size reasonable
        if len(self._buffer) > max_size:
            self._buffer = self._buffer[-max_size:]

    def extract_measurement(self) -> OximeterMeasurement | None:
        """Extract a measurement from the buffer if available.

        This is called periodically by the coordinator's poll method.
        """
        frame_header = self.device_info.frame_header
        frame_length = self.device_info.frame_length

        # Look for frame header
        idx = self._buffer.find(frame_header)
        if idx < 0:
            return None  # No header found

        # Remove everything before the header
        if idx > 0:
            self._buffer = self._buffer[idx:]

        # Check if we have a complete frame
        if len(self._buffer) < frame_length:
            return None  # Not enough data yet

        # Extract the frame
        frame = bytes(self._buffer[:frame_length])
        self._buffer = self._buffer[frame_length:]  # Remove consumed data from buffer

        # Validate and decode the frame
        try:
            if not frame.startswith(frame_header):
                return None

            # Verify checksum
            if not self._verify_checksum(frame):
                return None

            measurement = self._decode_frame(frame)
            self.last_measurement = measurement
            return measurement
        except Exception:
            # Skip invalid frames and try again with next data
            return None

    def _verify_checksum(self, frame: bytes) -> bool:
        """Verify JKS50F frame checksum.

        Checksum algorithm: (sum of all bytes except checksum + 1) & 0xFF
        The checksum is the last byte of the frame.
        """
        if len(frame) < 2:
            return False

        data = frame[:-1]  # All bytes except the last one
        checksum = frame[-1]  # Last byte is the checksum

        calculated = (sum(data) + 1) & 0xFF
        is_valid = calculated == checksum

        if not is_valid:
            _LOGGER.debug("Checksum mismatch for frame: %s", frame.hex())

        return is_valid

    def _decode_frame(self, frame: bytes) -> OximeterMeasurement:
        """Decode a complete JKS50F frame."""
        if len(frame) < 8:
            raise ValueError(f"Frame too short: {len(frame)} bytes")

        # Byte 3: Finger flag (0 = Finger present, !=0 = no finger)
        finger = not bool(frame[3])

        # Byte 4: SpO2 value
        spo2 = int(frame[4])
        if spo2 == 127:
            spo2 = None

        # Byte 5: Pulse rate
        pr = int(frame[5])
        if pr == 127:
            pr = None

        # Perfusion Index from Byte 6+7
        byte6_7bit = frame[6] & 0b0111_1111
        byte7_6bit = frame[7] & 0b0011_1111
        pi = (byte6_7bit | (byte7_6bit << 7)) / 100
        if pi == 81.91:  # Invalid value marker
            pi = None
        elif pi > 20.0:
            pi = None  # Unrealistic high value

        return OximeterMeasurement(
            finger_present=finger,
            spo2=spo2,
            pulse=pr,
            perfusion_index=pi,
            timestamp=datetime.now(),
        )
