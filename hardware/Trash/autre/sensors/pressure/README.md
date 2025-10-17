# Pressure Sensor Implementation

This directory will contain pressure monitoring sensor implementations for the MOLONARI ecosystem.

## Planned Features

- **Differential Pressure Measurement**: For water flow calculations
- **High-Resolution Sensors**: Capable of detecting small pressure changes
- **Underwater Operation**: Waterproof sensors for riverbed deployment
- **Low-Power Design**: Long-term autonomous operation

## Development Status

🚧 **Under Development** - This sensor type is planned for future implementation.

## Hardware Requirements

- Arduino MKR WAN 1310
- Differential pressure sensor module
- Waterproof pressure ports
- SD card for data logging
- LoRa antenna for communication

## Integration

Pressure sensors will use the same shared libraries and communication protocols as temperature sensors:

- `../../shared/Lora.hpp` - LoRa communication
- `../../shared/Pressure_Sensor.hpp` - Pressure sensor drivers  
- `../../shared/Writer.hpp` - Data logging
- `../../shared/Low_Power.hpp` - Power management

## Contributing

If you're interested in developing pressure sensor functionality:

1. Review the temperature sensor implementation in `../temperature/`
2. Study the shared pressure sensor library in `../../shared/Pressure_Sensor.hpp`
3. Follow the same code structure and commenting conventions
4. Test with the hardware validation CI workflow

For questions or collaboration, please open an issue on GitHub.