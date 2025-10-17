# LoRaWAN Protocol Implementation

This directory contains LoRaWAN integration for wide-area network connectivity in the MOLONARI ecosystem.

## Protocol Overview

LoRaWAN provides **long-range, low-power wide-area network (LPWAN) connectivity** for relay-to-gateway communication:

- **Standard Protocol**: Industry-standard LoRaWAN implementation
- **Wide Coverage**: Kilometers range for gateway connectivity  
- **Internet Bridge**: Connects to The Things Network (TTN) for server access
- **Encrypted Communication**: Built-in security for data transmission

## Current Implementation

### Relay-to-Gateway Communication

The relay stations use LoRaWAN to forward aggregated sensor data to internet-connected gateways:

- **Demo Implementation**: Available in `../../sensors/demo/Relay_LoraWan/`
- **Standard Libraries**: Uses Arduino MKRWAN library
- **TTN Integration**: Configured for The Things Network

### Hardware Requirements

- **Arduino MKR WAN 1310**: Built-in LoRaWAN capability
- **LoRaWAN Gateway**: Robustel R3000 or compatible
- **Network Server**: The Things Network (TTN) or private server

## Configuration

### Gateway Setup

Gateway configuration is documented in:

- **`../../docs/5 - Gateway and server configurations.md`**: Complete setup guide
- Covers TTN account creation, device registration, and gateway configuration

### Device Registration

Each relay must be registered with the LoRaWAN network:

1. **Create TTN Application**: Group devices under single application
2. **Register End Devices**: Add each relay with unique DevEUI
3. **Configure Keys**: Set AppEUI and AppKey for secure communication
4. **Gateway Registration**: Connect gateway to TTN network

## Testing

LoRaWAN connectivity testing:

- **`../../tests/testArduinoLoRaWAN/`**: Basic LoRaWAN connectivity test
- **`../../sensors/demo/Relay_LoraWan/`**: Demo relay with LoRaWAN

### Test Procedure

```bash
cd ../../tests/testArduinoLoRaWAN
arduino-cli compile --fqbn arduino:samd:mkrwan1310 testArduinoLoRaWAN.ino
arduino-cli upload --fqbn arduino:samd:mkrwan1310 testArduinoLoRaWAN.ino --port /dev/ttyACM0
```

## Network Architecture

```
Sensors → Relay → LoRaWAN Gateway → TTN → Internet → Server
```

- **Local Network**: Custom LoRa protocol (sensor ↔ relay)
- **Wide Area**: LoRaWAN protocol (relay ↔ gateway)
- **Internet**: HTTP/HTTPS (gateway ↔ server)

## Frequency Bands

- **Europe**: 868 MHz
- **North America**: 915 MHz
- **Asia**: 923 MHz (varies by country)

Configure frequency in Arduino code based on deployment region.

## Data Rate and Power

LoRaWAN automatically optimizes:

- **Adaptive Data Rate (ADR)**: Optimizes data rate based on link conditions
- **Transmission Power**: Minimizes power consumption while maintaining reliability
- **Duty Cycle**: Complies with regional regulations (1% in EU)

## Integration with Custom LoRa

The MOLONARI system uses a **hybrid approach**:

1. **Local Communication**: Custom LoRa protocol for sensor-relay communication
   - Optimized for underwater environment
   - Power-efficient scheduled transmissions
   - Custom retry logic

2. **Wide Area Communication**: Standard LoRaWAN for relay-gateway communication
   - Industry-standard protocol
   - Internet connectivity
   - Encrypted data transmission

## Future Enhancements

- **Direct LoRaWAN Sensors**: Skip relay for simple deployments
- **Private LoRaWAN Network**: Dedicated network server for large installations
- **Class B/C Support**: Synchronized and continuous reception modes
- **Over-the-Air Updates**: Remote firmware updates via LoRaWAN

## Development

To modify LoRaWAN implementation:

1. Review current demo in `../../sensors/demo/Relay_LoraWan/`
2. Test connectivity with `../../tests/testArduinoLoRaWAN/`
3. Update gateway configuration following documentation
4. Validate end-to-end communication

## Troubleshooting

### Common Issues

1. **Join Failed**: Check DevEUI, AppEUI, and AppKey configuration
2. **No Coverage**: Verify gateway proximity and network coverage
3. **Duty Cycle Exceeded**: Reduce transmission frequency or data size
4. **Invalid Frequency**: Verify frequency band for deployment region

### Debugging

- Enable debug output in Arduino code
- Monitor TTN console for device activity
- Check gateway logs for connectivity issues
- Verify antenna connections and placement

See the main hardware README and gateway configuration documentation for detailed troubleshooting procedures.