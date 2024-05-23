"""Entity for a Covers powered by simple Relays controlled via MQTT protocol.

This module provides an entity class for controlling covers powered by simple relays
and controlled through MQTT messages. The `MQTTRelayCover` class represents a cover entity
that supports opening, closing, stopping, and setting the position of the cover.

The cover position is represented as a percentage, where 0% indicates a fully closed
position and 100% indicates a fully open position. The class assumes constant speed for
cover movement and may not account for external factors such as network latency or physical
limitations.

Features:
- Opening and closing times can be pre-configured.
- Supports MQTT integration for control and monitoring.
- Calibration support.

Note:
- Tilt operations are not supported.

Usage:
1. Instantiate the `MQTTRelayCover` class with the required parameters.
2. Use the provided methods to control and monitor the state of the cover.

Note:
- The `MQTTRelayCover` class inherits from the `CoverEntity` class provided by Home Assistant.
- The class assumes that the MQTT broker and topics are properly configured in Home Assistant.

Args:
    object_id (str): The unique identifier for the entity. Used as a fallback for naming and
 as part of the unique_id if not provided in `entity_config`.
    entity_config (ConfigType): The configuration for the entity. Expected to contain keys
like `CONF_FRIENDLY_NAME`, `CONF_UNIQUE_ID`, `CONF_OPENING_TIME`, and `CONF_CLOSING_TIME`,
among others. Opening and closing times are expected in milliseconds.

Attributes:
- `should_poll`: A boolean indicating whether the entity should be polled for updates.
- `_attr_supported_features`: A bitmask representing the supported features of the cover entity.

Methods:
- `set_opening`: Set the opening state of the cover.
- `set_closing`: Set the closing state of the cover.
- `is_stopped`: Check if the cover is currently stopped.
- `is_closed`: Check if the cover is closed.
- `async_set_cover_position`: Move the cover to a specific position using MQTT commands.

"""

import asyncio
import logging
import time

from homeassistant.components import mqtt
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.components.mqtt import async_publish
from homeassistant.const import CONF_FRIENDLY_NAME, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CLOSING_TIME,
    CONF_MQTT_COMMAND_TOPIC,
    CONF_MQTT_PAYLOAD_CLOSE,
    CONF_MQTT_PAYLOAD_OPEN,
    CONF_MQTT_PAYLOAD_STOP,
    CONF_OPENING_TIME,
    DOMAIN,
    SERVICE_CALIBRATE,
)

_LOGGER = logging.getLogger(__name__)

_CHECK_INTERVAL = 0.1  # interval in seconds to check if cover needs to be stopped
_MIN_POSITION = 0
_MAX_POSITION = 100
_MAX_PERCENT = 100
_MILISECONDS_IN_SECOND = 1000.0
_DEFAULT_NAME = "MQTT Relay Cover"


class MQTTRelayCover(CoverEntity):
    """Representation of a cover powered by simple relays controlled by MQTT.

    This class represents a cover entity that is powered by simple relays and controlled
    through MQTT messages. It inherits from the CoverEntity class and provides methods
    and attributes to control and monitor the state of the cover.

    The cover can be opened, closed, stopped, and set to a specific position. It supports
    features such as pre-configured opening and closing times, calibration, and MQTT integration.
    Note that **tilt** operations are not supported.

    Note:
    - The cover position is represented as a percentage, where 0% indicates a fully closed
      position and 100% indicates a fully open position.
    - The class assumes constant speed for cover movement and may not account for external
      factors such as network latency or physical limitations.

    Args:
        object_id (str): The unique identifier for the entity. Used as a fallback for
    naming and as part of the unique_id if not provided in `entity_config`.
        entity_config (ConfigType): The configuration for the entity. Expected to contain
    keys like `CONF_FRIENDLY_NAME`, `CONF_UNIQUE_ID`, `CONF_OPENING_TIME`, and
    `CONF_CLOSING_TIME`, among others. Opening and closing times are expected in miliseconds.

    """

    # Tell HA to not poll this entity, as we're updating it ourselves
    should_poll = False

    # Currently supported features for the cover entity. No tilt support.
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
    )

    def __init__(self, object_id: str, entity_config: ConfigType) -> None:
        """Initialize the MQTT Relay Cover entity.

        Sets up the MQTT Relay Cover with unique identifiers and configuration parameters
        such as opening and closing times. It prepares the entity for operation by
        initializing state attributes and acquiring necessary configuration details
        from `entity_config`.

        Args:
            object_id (str): The unique identifier for the entity. Used as a fallback
        for naming and as part of the unique_id if not provided in `entity_config`.
            entity_config (ConfigType): The configuration for the entity. Expected to
        contain keys like `CONF_FRIENDLY_NAME`, `CONF_UNIQUE_ID`, `CONF_OPENING_TIME`,
        and `CONF_CLOSING_TIME`, among others. Opening and closing times are expected in
        milliseconds.

        """
        self._lock = asyncio.Lock()
        self._attr_is_closing = False
        self._attr_is_opening = False
        # 0 is closed, 100 is open, values are set in percents (%)
        self._attr_current_cover_position: int | None = None

        self.unique_id: str = entity_config.get(CONF_UNIQUE_ID, object_id)
        self._attr_name = entity_config.get(
            CONF_NAME,
            entity_config.get(CONF_FRIENDLY_NAME, _DEFAULT_NAME + self.unique_id),
        )
        self._attr_friendly_name = entity_config.get(
            CONF_FRIENDLY_NAME,
            entity_config.get(CONF_NAME, _DEFAULT_NAME + self.unique_id),
        )

        self._store: Store | None = None

        self._opening_time: float = (
            entity_config.get(CONF_OPENING_TIME, 0) / _MILISECONDS_IN_SECOND
        )
        self._closing_time: float = (
            entity_config.get(CONF_CLOSING_TIME, self._opening_time)
            / _MILISECONDS_IN_SECOND
        )
        self._mqtt_command_topic: str = entity_config.get(CONF_MQTT_COMMAND_TOPIC)
        self._mqtt_payload_open: str = entity_config.get(CONF_MQTT_PAYLOAD_OPEN)
        self._mqtt_payload_close: str = entity_config.get(CONF_MQTT_PAYLOAD_CLOSE)
        self._mqtt_payload_stop: str = entity_config.get(CONF_MQTT_PAYLOAD_STOP)

    async def async_added_to_hass(self):
        """Handle when an entity is added to Home Assistant.

        This method is called by Home Assistant when the entity is added to the system.
        It is used to initialize the entity and perform any necessary setup.

        If the entity has previously been added and stored in the data store, the stored
        cover position is retrieved and set as the current cover position. Otherwise, the
        current cover position is set to the default value of 0.

        """
        self._store = Store(self.hass, version=1, key=DOMAIN)
        stored_data = await self._store.async_load()
        self._attr_current_cover_position = stored_data.get(self.unique_id, 0)

        # Register the calibrate service
        self.platform.async_register_entity_service(
            SERVICE_CALIBRATE,
            {},
            "async_calibrate",
        )

    def set_opening(self, opening: bool) -> None:
        """Set the opening state of the cover."""
        self._attr_is_opening = opening

    def set_closing(self, closing: bool) -> None:
        """Set the closing state of the cover."""
        self._attr_is_closing = closing

    @property
    def is_stopped(self) -> bool:
        """Return if the cover is currently stopped."""
        return not self._attr_is_opening and not self._attr_is_closing

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self._attr_current_cover_position == 0

    async def async_set_cover_position(self, **kwargs) -> None:
        """Asynchronously move the cover to a specific position using MQTT commands.

        This method stops any ongoing movement, calculates the direction - opening or
        closing, and moves the cover accordingly. It monitors and adjusts
        the movement in real-time every `_CHECK_INTERVAL` period until the target
        position is reached, the maximum movement time is exceeded, or an external
        stop/change direction command is received.

        Args:
            **kwargs: Keyword arguments. Must include 'position', an integer
        specifying the target position for the cover as a percentage (0-100).

        Note:
        - The method utilizes a lock (`self._lock`) to prevent concurrent
        command execution, ensuring consistent state and command order.
        - The actual movement is simulated through time-based progress
        calculation, which assumes constant speed. Network latency or other
        external factors could affect actual movement.

        """

        # Initial preparation: Stops any ongoing movement to reset states.
        # Setting both opening and closing to False allows exiting out of
        # the critical section, so this enables correct behaviour even if
        # multiple *set_cover_position* calls are made in parallel.
        await self.async_stop_cover()

        try:
            # Critical section starts here, the only variables that can be changed
            # outside that block are `_attr_is_opening`, `_attr_is_closing` and
            # `_attr_current_cover_position`. First two are used to make cover
            # stop or to change the movment direction at any moment.
            async with self._lock:
                # Extract the target position, defaulting to 0 if not specified.
                # Ensure that the target position is between 0 and 100%.
                target_position = max(
                    min(kwargs.get("position", 0), _MAX_POSITION), _MIN_POSITION
                )

                # Memorise starting position
                initial_position = self._attr_current_cover_position

                # Fixate the time when we started the cover move
                start_moving_time = time.monotonic()

                # Determine movement direction and update state accordingly
                is_opening_direction = target_position > initial_position
                self.set_opening(is_opening_direction)
                self.set_closing(not is_opening_direction)

                # Calculate maximum expected movement duration based on direction
                movement_time = (
                    self._opening_time if is_opening_direction else self._closing_time
                )

                # Initiate movement in the determined direction
                await self.__async_publish(
                    self._mqtt_payload_open
                    if is_opening_direction
                    else self._mqtt_payload_close
                )

                # Monitor movement progress and adjust position in real-time.
                # Loop until we either:
                # 1. Exceed defined time to reach the limit position, either
                #  absolutely open or absolutely closed (the time is up)
                # 2. Reach out the desired target position or 100% for opening or 0%
                #  for closing - whatever comes first
                # 3. The state for opening become False while opening
                #  OR the state for closing become False while closing
                while (
                    (now := time.monotonic()) < start_moving_time + movement_time
                ) and (
                    (
                        self.is_opening
                        and self._attr_current_cover_position < target_position
                    )
                    or (
                        self.is_closing
                        and self._attr_current_cover_position > target_position
                    )
                ):
                    await asyncio.sleep(_CHECK_INTERVAL)

                    time_elapsed = now - start_moving_time
                    progress = time_elapsed / movement_time * _MAX_PERCENT
                    self._attr_current_cover_position = (
                        min(initial_position + progress, target_position)
                        if is_opening_direction
                        else max(initial_position - progress, target_position)
                    )
                    self.async_write_ha_state()

                # Save new cover position
                await self._store.async_save(
                    {self.unique_id: self._attr_current_cover_position}
                )
        finally:
            # Ensure that the cover is stopped and set correct states
            await self.async_stop_cover()

    async def async_open_cover(self, **kwargs):
        """Open the cover until it reaches the maximum position.

        This method asynchronously opens the cover until it reaches the maximum position.
        The maximum position is defined by the constant MAX_POSITION.

        """
        await self.async_set_cover_position(position=_MAX_POSITION)

    async def async_close_cover(self, **kwargs):
        """Close the cover until it reaches the minimum position.

        This method asynchronously closes the cover until it reaches the minimum position.
        The minimum position is defined by the constant MIN_POSITION.

        """
        await self.async_set_cover_position(position=_MIN_POSITION)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover.

        This method stops the cover by setting the opening and closing flags to False,
        and publishes the MQTT payload for stopping the cover. It also updates the
        Home Assistant state.

        """
        self.set_opening(False)
        self.set_closing(False)
        await self.__async_publish(self._mqtt_payload_stop)
        # Don't forget to update the state
        self.async_write_ha_state()

    async def __async_publish(self, payload: str) -> None:
        """Publish a payload to the MQTT command topic.

        This method publishes the provided payload to the MQTT command topic.
        It first checks if MQTT is available by calling the __isMQTTAvailable method.
        If MQTT is available, it uses the async_publish function to publish the payload.

        Args:
            payload (str): The payload to be published.

        """
        if await self.__isMQTTAvailable():
            await async_publish(
                self.hass, topic=self._mqtt_command_topic, payload=payload
            )

    async def __isMQTTAvailable(self) -> bool:
        """Check if MQTT integration is available and loaded in Home Assistant.

        Returns:
            bool: True if MQTT integration is available and loaded, False otherwise.

        """
        return (
            await self.hass.config_entries.async_wait_component(
                self.hass.config_entries.async_entries(mqtt.DOMAIN)[0]
            )
            if self.hass.config_entries.async_entries(mqtt.DOMAIN)
            else _LOGGER.error("MQTT integration is not available")
        )

    async def async_calibrate(self, **kwargs) -> None:
        """Calibrates the cover's initial position.

        This method is used to calibrate the cover and establish a full correspondence
        between the set position of the cover and its physical position. It is typically
        used for initial configuration or to correct the physical position and its logical
        representation after adjustments made outside of Home Assistant, such as manual
        adjustments or after some messy power outages.

        Note that this method is not intended to be used on a regular basis, but rather as
        a one-time or occasional procedure to ensure accurate positioning of the cover.

        During calibration, a lock is acquired to prevent any other procedures with the
        cover from being executed until the calibration is finished. The cover is set to
        the closed position, then opened briefly, and finally closed again. The current
        cover position is set to 0, indicating a fully closed state.

        After calibration, the current cover position is saved and the Home Assistant
        state is updated.

        """
        async with self._lock:
            self.set_opening(False)
            self.set_closing(False)
            await self.__async_publish(self._mqtt_payload_open)
            await asyncio.sleep(self._opening_time + 1)
            await self.__async_publish(self._mqtt_payload_stop)
            await asyncio.sleep(1)
            await self.__async_publish(self._mqtt_payload_close)
            await asyncio.sleep(self._closing_time + 1)
            await self.__async_publish(self._mqtt_payload_stop)
            await asyncio.sleep(1)
            self._attr_current_cover_position = 0
            await self._store.async_save(
                {self.unique_id: self._attr_current_cover_position}
            )
            self.async_write_ha_state()
