# LoRa Protocol Implementation

This directory contains the custom LoRa communication protocol implementation for local sensor-to-relay communication in the MOLONARI ecosystem.

## Protocol Overview

The MOLONARI LoRa protocol implements a **reliable, low-power communication system** for underwater sensor networks:

- **Three-way handshake**: SYN → ACK → DATA → FIN
- **Scheduled communication**: Daily transmission windows (e.g., 23:45 for temperature sensors)
- **Retry mechanism**: Up to 6 attempts with exponential backoff
- **Tree topology**: Multiple sensors per relay (up to 10 devices)
- **Range**: 100m underwater, 1km+ surface

## Protocol Implementation

### Core Classes

The protocol is implemented in the shared libraries:

- **`../../shared/Lora.hpp`**: Main protocol implementation
- **`../../shared/Lora.cpp`**: Protocol logic and state machine

### Message Types

```cpp
enum RequestType : uint8_t {
    SYN = 0xcc,  // Synchronization request
    ACK = 0x33,  // Acknowledgment response  
    DATA = 0xc3, // Data transmission
    FIN = 0x3c   // End of transmission
};
```

### Communication Flow

1. **Sensor Wake-up**: Sensor initiates communication at scheduled time
2. **Handshake**: Three-way handshake establishes session
3. **Data Transfer**: Sensor transmits collected measurements
4. **Acknowledgment**: Relay confirms receipt
5. **Sleep**: Sensor returns to low-power mode

## Testing

Protocol testing is available in the tests directory:

- **`../../tests/Sensor_Lora/`**: Sensor-side protocol testing
- **`../../tests/Relay_Lora/`**: Relay-side protocol testing
- **`../../tests/Sender/`**: Basic LoRa sender test
- **`../../tests/Receiver/`**: Basic LoRa receiver test

## Documentation

Detailed protocol documentation is available:

- **`../../docs/4 - Our LoRa protocol_ENG.md`**: Complete protocol specification
- **`../../docs/3 - Sensor's hardware-ENG.md`**: Hardware implementation details

## Future Enhancements

- **Mesh networking**: Multi-hop communication via relay nodes
- **Adaptive power control**: Dynamic transmission power based on link quality
- **Frequency hopping**: Improved reliability in noisy environments
- **Encryption**: Secure data transmission

## Development

To modify the LoRa protocol:

1. Edit `../../shared/Lora.hpp` and `../../shared/Lora.cpp`
2. Test changes with sender/receiver pairs
3. Validate with sensor/relay integration tests
4. Update protocol documentation

See the main hardware README for development workflows and testing procedures.