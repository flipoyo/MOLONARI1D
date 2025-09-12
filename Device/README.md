# Device - MOLONARI1D Hardware Components

This directory contains the hardware specifications, firmware development, and installation systems for the MOLONARI1D environmental monitoring platform.

## Directory Overview

### `hardware/` - Physical Device Specifications
Contains detailed specifications and design documents for the physical monitoring devices:
- **dataloggerAndRelay/**: Data logging and relay station hardware designs
- **differentialPressureSensor/**: Pressure measurement device specifications  
- **distributedTemperatureSensor/**: Temperature sensor array designs

### `hardwareProgramming/` - Historical Firmware Development
Original firmware development directory containing legacy code and documentation:
- **Sensor/**: Original sensor firmware implementations
- **Relay/**: Original relay station implementations  
- **Documentation/**: Complete technical documentation and guides
- **Archive_before/**: Historical development contributions

### `installationSystem/` - Field Deployment
Installation procedures and field deployment documentation:
- Manual installation guides for sensor deployment
- Mechanical systems for device installation (pipe ramming, etc.)
- Field maintenance and troubleshooting procedures

## Relationship with `hardware/` Directory

For improved development workflows, this repository now includes a reorganized `hardware/` directory at the root level that:

1. **Consolidates** duplicated code from multiple `internals/` directories
2. **Organizes** by development team and functionality
3. **Modernizes** the development workflow with CI/CD integration
4. **Maintains** full backward compatibility with existing code

### Migration Mapping

| Device/ Structure | New hardware/ Structure | Purpose |
|-------------------|------------------------|---------|
| `hardwareProgramming/Sensor/` | `hardware/sensors/` | Sensor firmware organized by type |
| `hardwareProgramming/Relay/` | `hardware/relay/` | Relay station implementations |
| `hardwareProgramming/Documentation/` | `hardware/docs/` | Consolidated documentation |
| `installationSystem/` | `hardware/deployment/` | Field deployment procedures |
| Multiple `internals/` dirs | `hardware/shared/` | Unified shared libraries |

## Development Workflows

### For New Development
Use the reorganized `hardware/` structure for new projects and features:
- Better team collaboration with organized directories
- Shared libraries eliminate code duplication
- Modern CI/CD integration for validation
- Comprehensive documentation and testing

### For Legacy Projects
The original `Device/` structure remains available for:
- Maintaining existing deployments
- Historical reference and documentation
- Specific hardware configurations already in the field

## Documentation Navigation

### Quick Access Guides
- [Hardware Installation Guide](hardwareProgramming/Documentation/1%20-%20Installation%20guide_ENG.md)
- [Sensor Hardware Overview](hardwareProgramming/Documentation/3%20-%20Sensor's%20hardware-ENG.md)
- [LoRa Protocol Specification](hardwareProgramming/Documentation/4%20-%20Our%20LoRa%20protocol_ENG.md)
- [Gateway Configuration](hardwareProgramming/Documentation/5%20-%20Gateway%20and%20server%20configurations.md)

### Hardware Specifications
- [Temperature Sensor Arrays](hardware/distributedTemperatureSensor/README.md)
- [Pressure Measurement Systems](hardware/differentialPressureSensor/README.md)
- [Data Logger and Relay Systems](hardware/dataloggerAndRelay/Readme.md)

### Installation and Deployment
- [Physical Installation Systems](installationSystem/README.md)
- [Field Deployment Procedures](../hardware/deployment/)
- [Maintenance and Troubleshooting](../hardware/docs/)

## Contributing

### For Hardware Development
1. Use the `hardware/` structure for new firmware development
2. Update shared libraries in `hardware/shared/` for common functionality
3. Add comprehensive tests in `hardware/tests/` for validation
4. Document all changes in the appropriate `hardware/docs/` section

### For Legacy Maintenance  
1. Continue using `Device/hardwareProgramming/` for existing deployments
2. Cross-reference with `hardware/shared/` for updated libraries
3. Consider migrating stable legacy code to the new structure

## Hardware Ecosystem

The MOLONARI1D hardware ecosystem supports:
- **Autonomous sensor networks** with 8-12 month battery life
- **Multi-hop LoRa communication** with relay stations
- **LoRaWAN gateway integration** for internet connectivity
- **Real-time data processing** and quality control
- **Scalable deployment** from single sites to river systems

For complete system architecture and integration details, see the [main repository README](../README.md) and [hardware programming guide](../hardware/README.md).