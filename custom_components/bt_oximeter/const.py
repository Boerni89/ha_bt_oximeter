from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "bt_oximeter"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

DEFAULT_NAME = "Pulse Oximeter"

# Config flow constants
CONF_MODEL = "model"

# Update interval for coordinator (extract data from buffer)
UPDATE_INTERVAL = timedelta(seconds=2)
