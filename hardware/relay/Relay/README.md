# LoRa Relay Station - Data Aggregation and Forwarding

This firmware implements the LoRa relay functionality for the MOLONARI1D monitoring system, serving as an intermediate data aggregation point between river bed sensors and the LoRaWAN gateway.

## Overview

The relay station collects sensor data from multiple underwater monitoring devices and forwards the aggregated information to the LoRaWAN gateway for internet transmission to the server.

## Hardware Requirements

- **Arduino MKR WAN 1310** - Main microcontroller with LoRa/LoRaWAN capabilities
- **External antenna** - High-gain antenna for extended range
- **Power supply** - Solar panel + battery system for autonomous operation
- **Weatherproof enclosure** - Protection for above-water installation

## Functionalities

### Current Features
- **Sensor Data Collection**: Request measurements from multiple sensors
- **LoRa Communication**: Custom protocol for sensor-to-relay communication
- **Serial Output**: Real-time data monitoring and debugging
- **Multi-sensor Management**: Handle up to 10 sensors per relay

### Planned Features (Long-term Roadmap)
- **LoRaWAN Gateway Integration**: Direct server communication
- **Data Buffering**: Local storage for offline scenarios
- **Adaptive Scheduling**: Dynamic measurement timing optimization
- **Mesh Networking**: Inter-relay communication for extended coverage

## Communication Architecture

### Sensor-to-Relay Protocol
- **Custom LoRa Protocol**: Optimized for low-power sensor communication
- **Request-Response Model**: Relay initiates communication with sensors
- **Collision Avoidance**: Time-division multiple access (TDMA)
- **Range**: Up to 1km surface, 100m underwater

### Network Topology
```
Sensors (underwater) → Relay (surface) → Gateway → Server
     LoRa                    LoRaWAN       Internet
```

## Configuration

### Basic Settings
```cpp
#define MEASURE_T double    // Measurement data type
#define DEBUG              // Enable serial debugging
// #define LORA_DEBUG      // Enable LoRa operation logs
```

### Communication Parameters
```cpp
uint8_t MyAddres = 0xaa;           // Relay station address
uint8_t defaultdestination = 0xff;  // Broadcast destination
LoraCommunication lora(868E6, MyAddres, defaultdestination);
```

## Operational Cycle

1. **Initialization**: Setup LoRa radio and communication parameters
2. **Sensor Discovery**: Identify active sensors in range
3. **Data Collection**: Sequential polling of registered sensors
4. **Data Aggregation**: Combine measurements with timestamps
5. **Forwarding**: Transmit to LoRaWAN gateway
6. **Status Monitoring**: Track sensor health and communication quality

## Power Management

- **Always-On Operation**: Relay stations require continuous power
- **Solar Charging**: Recommended 20W panel with 12V battery
- **Low-Power LoRa**: Optimized duty cycles for sensor communication
- **Adaptive Scheduling**: Reduce polling frequency during low activity

## Installation Guidelines

### Site Selection
- **Elevated Position**: Clear line-of-sight to sensor locations
- **Gateway Coverage**: Within LoRaWAN range (typically 2-10km)
- **Power Access**: Solar panel placement or grid connection
- **Environmental Protection**: Weatherproof mounting

### Configuration Steps
1. Install Arduino libraries and dependencies
2. Configure relay address and sensor network parameters
3. Upload firmware and verify serial output
4. Deploy in field location with appropriate antenna
5. Test communication with sensors and gateway

## File Structure

```
Relay/
├── Relay.ino                    # Main relay firmware
└── Dependencies:
    ├── ../../shared/Lora.hpp    # LoRa communication library
    └── ../../shared/Waiter.hpp  # Timing and scheduling utilities
```

## Debug and Monitoring

### Serial Output
- Real-time sensor data display
- Communication status monitoring
- Error reporting and diagnostics

### LED Indicators
- **Initialization**: LED on during startup
- **Communication**: Visual feedback for LoRa operations
- **Error States**: Flash patterns for troubleshooting

## Network Scalability

- **Sensor Capacity**: Up to 10 sensors per relay
- **Coverage Area**: 1km² surface, 0.1km² underwater
- **Data Throughput**: 1KB per sensor per day
- **Expansion**: Multiple relays for large river systems

## Related Documentation

- [Sensor Communication Protocol](../../protocols/lora-protocol.md)
- [LoRaWAN Integration Guide](../../protocols/lorawan-integration.md)
- [Field Installation Manual](../../deployment/relay-installation.md)
- [Network Planning Guide](../../docs/network-design.md)