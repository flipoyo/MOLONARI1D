# Sensor Demo - River Bed Monitoring System

This is the demonstration firmware for the Arduino-based river bed sensors in the MOLONARI1D environmental monitoring system.

## Overview

This firmware demonstrates the complete sensor functionality including temperature and pressure measurements, LoRa transmission, and local data storage for underwater deployment scenarios.

## Hardware Requirements

- **Arduino MKR WAN 1310** - Main microcontroller with LoRa capabilities
- **Featherwing Adalogger** - SD card storage for local data backup
- **Temperature sensors** - DS18B20 or similar waterproof sensors
- **Pressure sensors** - Differential pressure measurement devices
- **LoRa antenna** - For communication with relay stations

## Functionalities

### Core Features
- **Temperature Measurements**: Multi-sensor support with high precision
- **Pressure Measurements**: Differential pressure for water level monitoring
- **LoRa Communication**: Wireless transmission to relay stations
- **SD Card Logging**: Local storage backup with CSV format
- **Power Management**: Low-power sleep modes for extended battery life

### Data Flow
1. **Sensor Reading**: Periodic measurements every 15 minutes
2. **Local Storage**: Immediate storage to SD card with timestamps
3. **LoRa Transmission**: Daily data upload to relay station
4. **Power Management**: Deep sleep between measurement cycles

## Configuration Options

### Debug Settings
```cpp
#define LORA_DEBUG      // Enable LoRa operation diagnostics
#define SD_DEBUG        // Enable SD card operation diagnostics
```

### Data Types
```cpp
#define MEASURE_T double          // Temperature measurement precision
#define MEASURE_P unsigned short  // Pressure measurement type
```

## Communication Protocol

- **Custom LoRa Protocol**: Three-way handshake for reliable transmission
- **Retry Mechanism**: Up to 6 attempts with exponential backoff
- **Data Validation**: Checksums and acknowledgment confirmation

## Power Consumption

- **Active Measurement**: ~50mA for 30 seconds every 15 minutes
- **LoRa Transmission**: ~120mA for 5 seconds daily
- **Deep Sleep**: <0.1mA continuous
- **Expected Battery Life**: 8-12 months on 5000mAh Li-ion

## Installation

1. Install required Arduino libraries:
   - LoRa
   - RTCZero
   - SD
   - OneWire
   - DallasTemperature
   - ArduinoLowPower

2. Configure sensor parameters in the code
3. Upload firmware to Arduino MKR WAN 1310
4. Deploy in waterproof enclosure with external sensors

## File Structure

```
Sensor_demo/
├── Sensor_demo.ino          # Main firmware file
└── internals/               # Shared library components
    ├── Lora.hpp             # LoRa communication
    ├── Temp_Sensor.hpp      # Temperature sensing
    ├── Pressure_Sensor.hpp  # Pressure sensing
    ├── Low_Power.cpp        # Power management
    ├── Time.cpp             # RTC operations
    ├── SD_Initializer.cpp   # SD card setup
    ├── Writer.hpp           # Data logging
    └── Waiter.hpp           # Timing control
```

## Usage

This demo showcases the complete sensor functionality for evaluation and testing before field deployment. The code demonstrates best practices for:

- Sensor calibration and validation
- Power-efficient measurement cycles
- Reliable wireless communication
- Data integrity and storage
- Environmental monitoring protocols

## Related Documentation

- [LoRa Protocol Specification](../../protocols/lora-protocol.md)
- [Hardware Assembly Guide](../../docs/assembly-guide.md)
- [Deployment Procedures](../../deployment/field-deployment.md)
- [Power Management](../../docs/power-management.md)