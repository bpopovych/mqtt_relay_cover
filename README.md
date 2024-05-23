# MQTT Relay Cover Control Integration

The MQTT Relay Cover Control is a custom integration for Home Assistant that allows you to control and track the position of relay-operated covers (such as shades and blinds) as if they were smart devices. By using basic MQTT commands to control these relays and integrating timing configurations, the system can intelligently manage cover positions and states. This integration sends MQTT messages to control the on/off relays that operate the covers and manages the position of covers based on the operating duration and initial configuration, which sets the full open and close durations for each device.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

**Control of Relay-Operated Covers**: Control your shades and blinds using basic on/off relay switches via MQTT messages.
**Smart Transformation**: Upgrade your simple relay controls into intelligent devices by managing the position of covers based on an initial configuration.
**Automation and Position Tracking**: Combine basic MQTT commands with timing configuration to smartly adjust the covers' positions and track their status, enabling automated control within Home Assistant.

## Prerequisites

- Home Assistant instance
- MQTT Broker setup and configured
- Relay-operated cover devices

## Installation

1. **Clone or Download the Integration**:

- Clone this repository into your Home Assistant's `custom_components` directory, or download the ZIP and extract it there.

```bash

cd path/to/your/homeassistant/config/custom_components

git clone https://github.com/bpopovych/mqtt_relay_cover.git

```

2. **Add Configuration to `configuration.yaml`**:

- Add the necessary configuration to your `configuration.yaml` file under the `mqtt_shade` domain.

3. **Restart Home Assistant**:

- Restart your Home Assistant instance to load the new integration.

## Configuration

Add the following configuration to your `configuration.yaml` file. Adjust the parameters according to your setup and preferences:

```yaml

cover:
  - platform: mqtt_relay_cover
  covers:
    office_left_shade:
      friendly_name: "Office Left Shade"
      unique_id: office_left_shade
      opening_time: 1500 # time in miliseconds to fully open
      closing_time: 2000 # time in miliseconds to fully close
      mqtt_command_topic: "your_mqtt_topic"
      mqtt_payload_open: "your_mqtt_open_payload"
      mqtt_payload_close: "your_mqtt_close_payload"
      mqtt_payload_stop: "your_mqtt_stop_payload"
    office_right_shade:
      friendly_name: "Office Right Shade"
      unique_id: office_right_shade
      opening_time: 1500
      closing_time: 2000
      mqtt_command_topic: "your_mqtt_topic"
      mqtt_payload_open: "your_mqtt_open_payload"
      mqtt_payload_close: "your_mqtt_close_payload"
      mqtt_payload_stop: "your_mqtt_stop_payload"
```

## Usage

Once configured, the shades can be controlled via the standard Home Assistant user interface. The custom services for calibration and position setting are also available:

- **Calibrate**: Ensures the shade's physical state matches the expected logical state.
- **SetPosition**: Manually sets the current position of a shade.

## Contributing

Contributions to this project are welcome! Please open an issue or submit a pull request on GitHub.

For any feedback or issues, please create an issue on the project's GitHub repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
