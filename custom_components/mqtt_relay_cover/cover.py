"""Platform for MQTT Relay Cover integration."""

import logging

import voluptuous as vol

from homeassistant.components.cover import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_COVERS,
    CONF_FRIENDLY_NAME,
    CONF_NAME,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_CLOSING_TIME,
    CONF_MQTT_COMMAND_TOPIC,
    CONF_MQTT_PAYLOAD_CLOSE,
    CONF_MQTT_PAYLOAD_OPEN,
    CONF_MQTT_PAYLOAD_STOP,
    CONF_OPENING_TIME,
)
from .mqtt_relay_cover import MQTTRelayCover

_LOGGER = logging.getLogger(__name__)

COVER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_FRIENDLY_NAME): cv.string,
        vol.Required(CONF_OPENING_TIME): cv.positive_int,
        vol.Optional(CONF_CLOSING_TIME): cv.positive_int,
        vol.Required(CONF_MQTT_COMMAND_TOPIC): cv.string,
        vol.Required(CONF_MQTT_PAYLOAD_OPEN): cv.string,
        vol.Required(CONF_MQTT_PAYLOAD_CLOSE): cv.string,
        vol.Required(CONF_MQTT_PAYLOAD_STOP): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COVERS): cv.schema_with_slug_keys(COVER_SCHEMA),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the MQTT Relay Cover.

    This function is responsible for setting up the MQTT Relay Cover component.
    It creates and adds MQTT relay covers based on the provided configuration.

    Args:
        hass (HomeAssistant): The Home Assistant core object.
        config (ConfigType): The configuration for the MQTT relay covers.
        async_add_entities (AddEntitiesCallback): Callback function to add entities.
        discovery_info (DiscoveryInfoType | None, optional): Discovery information.

    """

    async_add_entities(
        [
            MQTTRelayCover(object_id, entity_config)
            for object_id, entity_config in config[CONF_COVERS].items()
            if not _LOGGER.info("Setting MQTT Relay Cover: %s", object_id)
        ]
    )
