from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_OPENING_TIME,
    CONF_CLOSING_TIME,
    CONF_MQTT_COMMAND_TOPIC,
    CONF_MQTT_PAYLOAD_OPEN,
    CONF_MQTT_PAYLOAD_CLOSE,
    CONF_MQTT_PAYLOAD_STOP,
)


class MQTTRelayCoverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MQTT Relay Cover."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, any] | None = None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=user_input.get("name", "MQTT Relay Cover"), data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required("name", default="MQTT Relay Cover"): str,
                vol.Required(CONF_OPENING_TIME): vol.Coerce(int),
                vol.Optional(CONF_CLOSING_TIME): vol.Coerce(int),
                vol.Required(CONF_MQTT_COMMAND_TOPIC): str,
                vol.Required(CONF_MQTT_PAYLOAD_OPEN): str,
                vol.Required(CONF_MQTT_PAYLOAD_CLOSE): str,
                vol.Required(CONF_MQTT_PAYLOAD_STOP): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MQTTRelayCoverOptionsFlow(config_entry)


class MQTTRelayCoverOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for MQTT Relay Cover."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, any] | None = None):
        """Manage the options for the custom component."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required("name", default=self.config_entry.data.get("name", "MQTT Relay Cover")): str,
                vol.Required(CONF_OPENING_TIME, default=self.config_entry.data.get(CONF_OPENING_TIME, 0)): vol.Coerce(int),
                vol.Optional(
                    CONF_CLOSING_TIME,
                    default=self.config_entry.data.get(CONF_CLOSING_TIME, self.config_entry.data.get(CONF_OPENING_TIME, 0)),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_MQTT_COMMAND_TOPIC,
                    default=self.config_entry.data.get(CONF_MQTT_COMMAND_TOPIC, ""),
                ): str,
                vol.Required(
                    CONF_MQTT_PAYLOAD_OPEN,
                    default=self.config_entry.data.get(CONF_MQTT_PAYLOAD_OPEN, ""),
                ): str,
                vol.Required(
                    CONF_MQTT_PAYLOAD_CLOSE,
                    default=self.config_entry.data.get(CONF_MQTT_PAYLOAD_CLOSE, ""),
                ): str,
                vol.Required(
                    CONF_MQTT_PAYLOAD_STOP,
                    default=self.config_entry.data.get(CONF_MQTT_PAYLOAD_STOP, ""),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
