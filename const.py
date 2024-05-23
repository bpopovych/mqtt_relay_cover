"""Constants for the MQTT Relay Cover Control integration."""

from typing import Final

DOMAIN: Final = "mqtt_relay_cover"

CONF_OPENING_TIME: Final = "opening_time"
CONF_CLOSING_TIME: Final = "closing_time"
CONF_MQTT_COMMAND_TOPIC: Final = "mqtt_command_topic"
CONF_MQTT_PAYLOAD_OPEN: Final = "mqtt_payload_open"
CONF_MQTT_PAYLOAD_CLOSE: Final = "mqtt_payload_close"
CONF_MQTT_PAYLOAD_STOP: Final = "mqtt_payload_stop"

SERVICE_CALIBRATE: Final = "calibrate"
