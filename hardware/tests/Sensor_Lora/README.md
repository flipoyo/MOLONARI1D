# Sensor LoRa Communication Test

Focused test script for debugging and refining the custom LoRa communication protocol between sensors and relay stations.

## Purpose

This test simulates sensor-side communication scenarios with non-real data to quickly debug and refine the protocol without requiring full system deployment or actual sensor hardware.

## Hardware Requirements

- **Arduino MKR WAN 1310** - Primary microcontroller
- **LoRa antenna** - For wireless communication testing
- **USB connection** - For serial debugging and monitoring

## Test Scenarios

### Protocol Validation
- Three-way handshake simulation
- Data packet creation and transmission
- Acknowledgment handling
- Retry mechanism testing

### Communication Features
- Simulated sensor data generation
- Protocol timing validation
- Error handling and recovery
- Queue management for data packets

## Configuration

```cpp
uint8_t MyAddress = 0xcc;  // Test sensor address
uint8_t RelayAdd = 0xaa;   // Target relay address
```

## Key Features

- **Non-real data simulation** for rapid protocol testing
- **Standard library queue** for packet management
- **LED feedback** during communication cycles
- **Serial debugging** for real-time monitoring
- **Protocol refinement** without full hardware setup

## Usage

1. Upload this firmware to an Arduino MKR WAN 1310
2. Configure the relay address to match your test relay
3. Monitor serial output for communication status
4. Use with corresponding Relay_Lora test for full validation

## Expected Output

The test validates:
- Successful LoRa initialization
- Packet creation and queuing
- Communication protocol execution
- Error handling and recovery
- Timing and synchronization

## Integration

This test is part of the broader hardware validation suite and supports:
- Protocol development and debugging
- Communication reliability testing
- Performance optimization
- Field deployment preparation