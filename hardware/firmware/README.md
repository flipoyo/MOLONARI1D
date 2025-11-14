# MOLONARI Hardware Programming

This directory contains all hardware-related documentation and code for the MOLONARI1D sensors network, organized for efficient collaboration between hardware developers, protocol engineers, and system integrators.

If you want to build a MOLONARI1D device, you can dive directly into the `docs/` folder.

## Directory Structure

```
hardware/
├── firmware/ 
│   ├── libs/                           # Librairies handmade for the project
│   │    ├── LoRa_Molonari/
│   │    ├── LoRaWan_Molonari/
│   │    ├── Measure/
│   │    ├── Reader/
│   │    ├── Time/
│   │    ├── Waiter/
│   │    └── Writer/
│   ├── mains/                          # Main codes we use    
│   │    └── relay/
│   │    │   ├── main.cpp
│   │    │   ├── config_relay.csv
│   │    │   └── README
│   │    └── sensor/
│   │        ├── main.cpp
│   │        ├── config_sensor.csv
│   │        └── README
├── tests/
│   ├── testArduinoLoRaWAN/  
│   ├── testArduinoLowPower/ 
│   ├── Sender/
│   ├── Receiver/
│   └── ...                  
├── docs/                               # Hardware documentation
│   ├── 1 - Installation guide_ENG.md
│   ├── 3 - Sensor's hardware-ENG.md
│   ├── 4 - Our LoRa protocol_ENG.md
│   └── ...
├── deployment/         
├── archived/               
│   ├── Archive_2022/
│   └── ...
└── README.md
```

For now, what works is the main_demo codes (one for the sensor and one for the relay). They can achieve almost everything we wanted to do for this year.

## Quick Start

### Prerequisites

- Platformio (to install on VScode)
- Arduino MKR WAN 1310 boards
- Pressure and temperature sensors
- SD cards
- Antenna
- ...


### Installation

1. **Install Platformio**
2. **Clone the repository**:
   ```bash
   git clone --depth=1 https://github.com/flipoyo/MOLONARI1D.git
   cd MOLONARI1D/hardware
   ```


3. Go into MOLONARI1D/hardware/mains_ino/sensor

- Fill the conf.csv file as in the README
- Upload on the arduino
- Fill the SD card with the csv file

4. Same with MOLONARI1D/hardware/mains_ino/relay but on the second arduino and SD

5. Place all sensors and the antenna on the sensor card

6. You're set up !



## Component Overview


### Libraries

The `/firmware/libs/` directory contains common code used across all hardware components.

It has its onw documentation it the repertory.


## Troubleshooting

### Common Issues

1. **Compilation Errors**:
   - Check Arduino board selection (arduino:samd:mkrwan1310)
   - Check the imports of the .ini file

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
- **Archived Code**: Reference `archived/` for historical implementations
- **Community**: Open issues on GitHub for support

## Contributing

### Code Standards

- **Commenting**: All Arduino files must have functionality header
- **Testing**: Validate compilation
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
- **SD card**

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

- **Protocol Improvements**: Mesh networking, adaptive power control
- **Gateway Integration**: Direct cellular connectivity

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