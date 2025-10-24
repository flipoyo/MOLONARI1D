# MOLONARI Hardware Programming

This directory contains all hardware-related documentation and code for the MOLONARI1D sensors network, organized for efficient collaboration between hardware developers, protocol engineers, and system integrators.

If you want to build a MOLONARI1D device, you can dive directly into the `docs/` folder.

## Directory Structure

```
hardware/
├── sensors/                  # Sensor node implementations
│   ├── temperature/
│   ├── pressure/
│   └── common/
├── relay/                    # Relay station implementations  
├── protocols/                # Communication protocol implementations
│   ├── lora/                 # Local LoRa communication
│   └── lorawan/              # Wide-area LoRaWAN communication
├── shared/                   # Shared libraries and utilities
│   ├── Lora.hpp/cpp
│   ├── Temp_Sensor.hpp/cpp
│   ├── Pressure_Sensor.hpp
│   ├── Writer.hpp/cpp
│   ├── Low_Power.hpp/cpp
│   └── ...
├── tests/                    # Hardware testing and validation
├── docs/                     # Hardware documentation
│   ├── 1 - Setup             # A complete guide to build a sensor
│   ├── 2 - Sensor code       # Explaining the sensor's code
│   ├── 3 - Sensor hardware   # Deep-diving into technical considerations
│   ├── 4 - Our LoRa protocol # Explaning the LoRa protocol
│   ├── 5 - Gateway and server configurations
│   ├── 6 - LoRaWAN           # Using the server
|   ├── deployment/           # Installation and deployment guides
|   └── specs/                # Hardware specifications
├── demo/                     # Demonstration and testing sensors
└── archived/                 # Historical code and contributions
```

## Quick Start

### Prerequisites

- Having read and followed the **INSTALL.md** guide
- **Arduino IDE** 2.x or **Arduino CLI**
- **Arduino MKR WAN 1310** boards
- Required libraries:
  - LoRa
  - MKRWAN
  - RTCZero
  - ArduinoLowPower
  - SD
  - OneWire
  - DallasTemperature

### Installation

1. **Compile and upload** sensor code:
   ```bash
   cd sensors/temperature/Sensor
   # Open Sensor.ino in Arduino IDE or use Arduino CLI:
   arduino-cli compile --fqbn arduino:samd:mkrwan1310 Sensor.ino
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 Sensor.ino --port /dev/ttyACM0
   ```

2. **Compile and upload** relay code:
   ```bash
   cd relay/Relay
   arduino-cli compile --fqbn arduino:samd:mkrwan1310 Relay.ino
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 Relay.ino --port /dev/ttyACM1
   ```

### Testing

Run hardware validation tests:
```bash
cd tests/testArduinoLoRaWAN
arduino-cli compile --fqbn arduino:samd:mkrwan1310 testArduinoLoRaWAN.ino
```

## Component Overview

### 🔍 Sensor Nodes

#### Temperature Sensors (`sensors/temperature/`):
- **Purpose**: Underwater temperature monitoring with 15-minute intervals
- **Hardware**: Arduino MKR WAN 1310 + DS18B20 sensors + SD card
- **Features**: 
  - Low-power operation (8-12 months battery life)
  - Local data storage with CSV format
  - Daily LoRa transmission to relay
  - Automatic retry mechanism (up to 6 attempts)

#### Demo Sensors (`sensors/demo/`):
- Simplified versions for testing and presentations
- Reduced functionality for rapid prototyping

### 🛜 Relay Stations

**Main Relay** (`relay/Relay/`):
- **Purpose**: Aggregate data from multiple sensor nodes
- **Communication**: 
  - Receives data via custom LoRa protocol
  - Forwards to gateway via LoRaWAN
- **Coverage**: Up to 10 sensors per relay, 1km range

### 🔗 Shared Libraries

The `shared/` directory contains common code used across all hardware components:

- **`Lora.hpp`**: Custom LoRa communication protocol implementation
- **`Temp_Sensor.hpp`**: Temperature sensor interface and drivers
- **`Writer.hpp`**: SD card logging with CSV format
- **`Low_Power.hpp`**: Power management and sleep modes
- **`Waiter.hpp`**: Timing and scheduling utilities

### 🗣️ Communication Protocols

#### Custom LoRa Protocol (sensor ↔ relay):
- Three-way handshake: SYN → ACK → DATA → FIN
- Scheduled transmission windows (daily at 23:45 for temperature)
- Retry mechanism with exponential backoff
- Tree topology support for scalability

#### LoRaWAN Protocol (relay ↔ gateway):
- Standard LoRaWAN implementation
- Wide-area coverage (kilometers)
- Internet connectivity via gateway

## Development Workflows

### For Hardware Developers

1. **Sensor Development**:
   - Create new sensor types in `sensors/[sensor_type]/`
   - Use shared libraries from `shared/` directory
   - Follow existing code structure and commenting conventions
   - Test with provided validation scripts

2. **Protocol Development**:
   - Modify communication protocols in `shared/Lora.hpp`
   - Update both sensor and relay implementations
   - Validate with `tests/Sender` and `tests/Receiver`

3. **Power Optimization**:
   - Use `Low_Power.hpp` utilities
   - Test power consumption with `tests/testArduinoLowPower`
   - Target 8-12 months battery life for sensors

### For Protocol Engineers

1. **LoRa Protocol Modification**:
   - Edit `shared/Lora.hpp` and `shared/Lora.cpp`
   - Update protocol documentation in `docs/4 - Our LoRa protocol_ENG.md`
   - Test with sender/receiver pairs

2. **LoRaWAN Integration**:
   - Modify relay LoRaWAN code
   - Update gateway configuration in `docs/5 - Gateway and server configurations.md`
   - Test end-to-end communication

### For System Integrators

1. **Deployment Planning**:
   - Review installation guides in `deployment/`
   - Plan sensor placement and relay coverage
   - Configure gateway connectivity

2. **Field Testing**:
   - Use demo sensors for initial validation
   - Test communication range and reliability
   - Validate power consumption in field conditions

## Testing and Validation

### Automated Testing

The hardware codebase includes CI/CD workflows:

- **Hardware Validation** (`.github/workflows/hardware-validation.yml`)
  - Compiles all Arduino code
  - Validates library dependencies
  - Checks code formatting and documentation

- **Protocol Testing** (`.github/workflows/protocol-tests.yml`)
  - Tests LoRa communication code
  - Validates LoRaWAN connectivity
  - Verifies protocol documentation

### Manual Testing

1. **Communication Range Testing**:
   ```bash
   # Terminal 1: Receiver
   cd tests/Receiver
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 Receiver.ino --port /dev/ttyACM0
   
   # Terminal 2: Sender  
   cd tests/Sender
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 Sender.ino --port /dev/ttyACM1
   ```

2. **Power Consumption Testing**:
   ```bash
   cd tests/testArduinoLowPower
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 testArduinoLowPower.ino
   # Measure current consumption with multimeter
   ```

3. **End-to-End System Testing**:
   - Deploy sensor and relay with actual hardware
   - Monitor communication logs
   - Validate data transmission to server

## Troubleshooting

### Common Issues

1. **Compilation Errors**:
   - Verify all required libraries are installed
   - Check Arduino board selection (arduino:samd:mkrwan1310)
   - Ensure shared library paths are correct

2. **Communication Failures**:
   - Check antenna connections
   - Verify frequency settings (868MHz EU, 915MHz US)
   - Test with shorter range first

3. **Power Issues**:
   - Verify battery voltage (>3.3V under load)
   - Check sleep mode implementation
   - Monitor current consumption

4. **SD Card Problems**:
   - Format SD card as FAT32
   - Check card compatibility (Class 10 recommended)
   - Verify CS pin connection (pin 5)

### Getting Help

- **Documentation**: Check `docs/` directory for detailed guides
- **Examples**: Review `tests/` directory for working examples
- **Archived Code**: Reference `archived/` for historical implementations
- **Community**: Open issues on GitHub for support

## Contributing

### Code Standards

- **Commenting**: All Arduino files must have functionality header
- **Include Paths**: Use shared libraries from `shared/` directory
- **Testing**: Validate compilation with Arduino CLI
- **Documentation**: Update relevant docs when modifying protocols

### Pull Request Process

1. Test your changes with hardware validation CI
2. Update documentation if modifying protocols
3. Ensure backward compatibility where possible
4. Follow existing code formatting conventions

## Hardware Specifications

### Target Hardware

- **Arduino MKR WAN 1310**: Main microcontroller platform
- **Adalogger FeatherWing**: SD card and RTC functionality
- **DS18B20**: Temperature sensors
- **Differential pressure sensors**: For flow measurement
- **LoRa antennas**: 868MHz (EU) or 915MHz (US)

### Power Requirements

- **Sensor Nodes**: 3.7V Li-ion battery (5000mAh recommended)
- **Relay Stations**: 12V battery or solar panel system
- **Expected Lifetime**: 8-12 months for sensor nodes

### Environmental Specifications

- **Operating Temperature**: -20°C to +60°C
- **Water Depth**: 0-10 meters
- **Enclosure Rating**: IP68 required for underwater deployment

## Future Development

### Planned Enhancements

- **Additional Sensor Types**: pH, conductivity, turbidity
- **Protocol Improvements**: Mesh networking, adaptive power control
- **Gateway Integration**: Direct cellular connectivity
- **Edge Computing**: Local data processing on relay stations

### Research Areas

- **Underwater Communication**: Improved antenna design
- **Energy Harvesting**: Solar and thermal energy collection
- **Data Compression**: Reduced transmission bandwidth
- **Fault Tolerance**: Redundant communication pathways

## Integration with Device/ Structure

This `hardware/` directory provides a reorganized, team-oriented view of the hardware components found in the original `Device/` structure:

- **hardware/** ↔ **Device/hardwareProgramming/** - Organized firmware development  
- **hardware/docs/** ↔ **Device/hardwareProgramming/Documentation/** - Consolidated documentation
- **hardware/deployment/** ↔ **Device/installationSystem/** - Field deployment guides
- **hardware/shared/** - Replaces duplicated `internals/` directories across projects

This reorganization maintains backward compatibility while improving development workflows and reducing code duplication.