"""TEMPLATE: Device implementation skeleton for new oximeter models.

INSTRUCTIONS:
1. Copy this file to a new file named after your device model (e.g., abc123.py)
2. Replace all TEMPLATE placeholders with your device's actual values
3. Implement the protocol-specific parsing logic
4. Test thoroughly with actual hardware
5. Add to SUPPORTED_DEVICES in devices/__init__.py
6. Update manifest.json with Bluetooth discovery info
"""
from __future__ import annotations

import logging
from datetime import datetime

from ..device_base import DeviceInfo, OximeterDeviceBase, OximeterMeasurement

_LOGGER = logging.getLogger(__name__)


class TEMPLATEDevice(OximeterDeviceBase):
    """Implementation for TEMPLATE pulse oximeter.

    REPLACE THIS: Add description of the device, manufacturer, and any
    specific quirks or behaviors that developers should know about.
    """

    def __init__(self) -> None:
        """Initialize TEMPLATE device."""
        super().__init__()
        # Buffer for incoming BLE notification data
        self._buffer: bytearray = bytearray()

        # TODO: Add any device-specific state variables here
        # Example: self._last_frame_time: float | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return TEMPLATE device metadata.

        REQUIRED: Update all fields with your device's actual values.
        You can find these by:
        1. Using a BLE scanner app (nRF Connect, LightBlue, etc.)
        2. Checking manufacturer documentation
        3. Analyzing similar devices
        4. Reverse engineering via packet captures
        """
        # REQUIRED: Full manufacturer name
        manufacturer = "TEMPLATE Manufacturer Name"
        # REQUIRED: Model identifier (shown in device selection)
        model = "TEMPLATE"
        # REQUIRED: Bytes that mark the start of a data frame
        # Example: b"\xff\x44\x01" or b"\xAA\xBB"
        # Find by analyzing received data patterns
        frame_header = b"\xFF\xFF"  # TODO: Replace with actual header
        # REQUIRED: Total length of one complete data frame in bytes
        # Example: 69, 32, 20
        # Find by analyzing complete packets
        frame_length = 20  # TODO: Replace with actual length
        # REQUIRED: BLE Service UUID
        # Example: "0000ffe0-0000-1000-8000-00805f9b34fb"
        # Find using BLE scanner app
        service_uuid = "00000000-0000-1000-8000-00805f9b34fb"  # TODO: Replace
        # REQUIRED: BLE Characteristic UUID for notifications
        # Example: "0000ffe1-0000-1000-8000-00805f9b34fb"
        # Find using BLE scanner app (look for notify/indicate properties)
        notify_uuid = "00000000-0000-1000-8000-00805f9b34fb"  # TODO: Replace
        # REQUIRED: MAC address OUI prefixes (first 6 hex digits)
        # Example: ["DC045A", "5414A7"]
        # Find by checking your device's MAC address
        # Used for device validation during discovery
        supported_ouis = [
            "000000",  # TODO: Replace with actual OUI(s)
        ]

        return DeviceInfo(
            manufacturer=manufacturer,
            model=model,
            frame_header=frame_header,
            frame_length=frame_length,
            service_uuid=service_uuid,
            notify_uuid=notify_uuid,
            supported_ouis=supported_ouis,
        )

    def add_to_buffer(self, data: bytes) -> None:
        """Add incoming BLE notification data to internal buffer.

        This is called from the notification handler and should be FAST.
        No parsing/decoding happens here - just buffer management.

        CUSTOMIZATION NOTES:
        - Most devices can use this simple implementation
        - Adjust max_size if your device sends large bursts
        - Consider time-based buffer expiry if needed
        - Add debug logging during development (remove for production)
        """
        # TODO: Uncomment for debugging during development
        # _LOGGER.debug("Received %d bytes: %s", len(data), data.hex())

        self._buffer.extend(data)
        max_size = 2 * self.device_info.frame_length

        # Keep buffer size reasonable - trim old data
        if len(self._buffer) > max_size:
            self._buffer = self._buffer[-max_size:]

    def extract_measurement(self) -> OximeterMeasurement | None:
        """Extract a measurement from buffered data if available.

        Called periodically by the coordinator (every 2 seconds).
        Returns None if no complete measurement is available yet.

        IMPLEMENTATION REQUIRED:
        This is where you implement your device's specific protocol parsing.
        The basic pattern (find header, extract frame, decode) works for
        most frame-based protocols, but you'll need to customize the
        validation and decoding logic.
        """
        frame_header = self.device_info.frame_header
        frame_length = self.device_info.frame_length

        # Step 1: Look for frame header in buffer
        idx = self._buffer.find(frame_header)
        if idx < 0:
            # No header found - wait for more data
            return None

        # Step 2: Remove garbage data before header
        if idx > 0:
            self._buffer = self._buffer[idx:]

        # Step 3: Check if we have a complete frame
        if len(self._buffer) < frame_length:
            # Incomplete frame - wait for more data
            return None

        # Step 4: Extract the frame
        frame = bytes(self._buffer[:frame_length])
        self._buffer = self._buffer[frame_length:]  # Remove from buffer

        # Step 5: Validate and decode the frame
        try:
            # Verify frame starts with expected header
            if not frame.startswith(frame_header):
                return None

            # Verify checksum (if your device has one)
            if not self._verify_checksum(frame):
                _LOGGER.debug("Checksum failed for frame: %s", frame.hex())
                return None

            # Decode the frame into measurement data
            measurement = self._decode_frame(frame)
            self.last_measurement = measurement
            return measurement

        except Exception as e:
            # Skip invalid frames and try again with next data
            _LOGGER.debug("Frame decode error: %s", e)
            return None

    def _verify_checksum(self, frame: bytes) -> bool:
        """Verify frame checksum/CRC.

        IMPLEMENTATION REQUIRED if your device uses checksums.

        Common checksum algorithms:

        1. Simple Sum:
           calculated = sum(frame[:-1]) & 0xFF
           return calculated == frame[-1]

        2. Sum + 1 (like JKS50F):
           calculated = (sum(frame[:-1]) + 1) & 0xFF
           return calculated == frame[-1]

        3. XOR:
           calculated = 0
           for byte in frame[:-1]:
               calculated ^= byte
           return calculated == frame[-1]

        4. CRC-8/CRC-16:
           Use appropriate library (crc8, crcmod)

        5. No checksum:
           return True
        """
        # TODO: Implement your device's checksum algorithm
        # For now, accept all frames (remove this in production!)

        # Example: Simple sum checksum
        # if len(frame) < 2:
        #     return False
        # calculated = sum(frame[:-1]) & 0xFF
        # return calculated == frame[-1]

        return True  # TODO: Replace with actual implementation

    def _decode_frame(self, frame: bytes) -> OximeterMeasurement:
        """Decode a complete frame into measurement data.

        IMPLEMENTATION REQUIRED:
        This is the core of your device support - extracting actual
        measurement values from the raw frame bytes.

        TIPS:
        - Log frames during development: _LOGGER.debug("Frame: %s", frame.hex())
        - Use hex editor to understand byte positions
        - Check for bit masks (finger detection often uses single bits)
        - Watch for invalid value markers (often 127, 255, or 0xFF)
        - Consider endianness (little-endian vs. big-endian for multi-byte values)
        """
        # Validate minimum frame length
        if len(frame) < self.device_info.frame_length:
            raise ValueError(f"Frame too short: {len(frame)} bytes")

        # TODO: Replace with your device's actual data extraction

        # Example 1: Finger detection (often a single bit)
        # Byte 3, bit 0: 0 = finger present, 1 = no finger
        finger = not bool(frame[3] & 0x01)

        # Example 2: SpO2 value (often a single byte, 0-100%)
        # Byte 4: SpO2 percentage, 127 = invalid
        spo2 = int(frame[4])
        if spo2 == 127 or spo2 > 100:  # Invalid markers
            spo2 = None

        # Example 3: Pulse rate (often a single byte or 7 bits + 1 bit)
        # Byte 5: Pulse rate BPM, 127 = invalid
        pulse = int(frame[5])
        if pulse == 127 or pulse > 250:  # Invalid markers
            pulse = None

        # Example 4: Perfusion Index (often 2 bytes, scaled)
        # Bytes 6-7: PI as 16-bit value, divided by 100 for percentage
        pi_raw = frame[6] | (frame[7] << 8)  # Little-endian
        pi = pi_raw / 100.0
        if pi > 20.0 or pi < 0:  # Unrealistic values
            pi = None

        # TODO: Add any other device-specific values
        # Examples: battery level, signal strength, bar graph, etc.

        return OximeterMeasurement(
            finger_present=finger,
            spo2=spo2,
            pulse=pulse,
            perfusion_index=pi,
            timestamp=datetime.now(),
        )


# TODO: After implementation, add to devices/__init__.py:
# from .template import TEMPLATEDevice
# SUPPORTED_DEVICES = {
#     "JKS50F": JKS50FDevice,
#     "TEMPLATE": TEMPLATEDevice,  # Add your device
# }

# TODO: Add Bluetooth discovery to manifest.json:
# {
#   "local_name": "YourDevice*",
#   "service_uuid": "your-service-uuid-here",
#   "connectable": true
# }
