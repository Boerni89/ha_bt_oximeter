"""Supported oximeter device implementations.

How to add a new device model:
1. Create a new file in this directory: devices/your_model.py
2. Implement OximeterDeviceBase with device-specific protocol:
   - device_info property (manufacturer, model, UUIDs, frame details)
   - add_to_buffer() method (buffer management for incoming BLE data)
   - extract_measurement() method (parse buffered data into OximeterMeasurement)
3. Import and add to SUPPORTED_DEVICES dict below
4. Add bluetooth discovery entry to manifest.json with device's service_uuid
5. Device will automatically appear in config flow dropdown
"""
from __future__ import annotations

from .jks50f import JKS50FDevice

# Registry of supported device models
# Format: "DISPLAY_NAME": DeviceClass
SUPPORTED_DEVICES = {
    "JKS50F": JKS50FDevice,
    # Example for adding new device:
    # "OTHER_MODEL": OtherModelDevice,
}

__all__ = ["SUPPORTED_DEVICES", "JKS50FDevice"]
