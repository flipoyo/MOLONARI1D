# Hardware Testing Suite

This directory contains comprehensive test programs for validating the MOLONARI1D hardware and communication protocols before field deployment.

## Test Categories

### Communication Protocol Tests

#### **Sensor_Lora** - Sensor Communication Testing
Focused test script for debugging and refining the custom LoRa protocol without requiring full system deployment.

**Purpose**: Validate sensor-to-relay communication
**Hardware**: Arduino MKR WAN 1310 with LoRa antenna
**Features**:
- Protocol debugging with simulated data
- Non-real sensor data for rapid testing
- Communication reliability validation

#### **Relay_Lora** - Relay Station Testing
Complementary test for validating relay station functionality and multi-sensor communication.

**Purpose**: Test relay aggregation and forwarding
**Hardware**: Arduino MKR WAN 1310 configured as relay
**Features**:
- Multi-device communication simulation
- Data collection and forwarding validation
- Network topology testing

#### **Sender/Receiver** - Basic LoRa Communication
Simple point-to-point LoRa communication tests for range and reliability validation.

**Purpose**: Baseline LoRa functionality verification
**Hardware**: Two Arduino MKR WAN 1310 devices
**Features**:
- Range testing in various environments
- Signal strength measurement
- Basic packet transmission validation

### System Component Tests

#### **testArduinoLoRaWAN** - LoRaWAN Gateway Integration
Validation of LoRaWAN connectivity for relay-to-gateway communication.

**Purpose**: Test wide-area network integration
**Hardware**: Arduino MKR WAN 1310 with LoRaWAN capability
**Features**:
- Network join procedures
- Gateway connectivity validation
- Internet data transmission testing

#### **testArduinoLowPower** - Power Management Validation
Critical testing for battery-powered sensor operation and power consumption optimization.

**Purpose**: Validate low-power operation modes
**Hardware**: Arduino MKR WAN 1310 with current measurement
**Features**:
- Deep sleep mode validation
- Power consumption measurement
- Wake-up cycle timing verification
- Battery life estimation

#### **Adjust_RTC** - Real-Time Clock Configuration
Precise timing system validation for synchronized measurements across the sensor network.

**Purpose**: RTC accuracy and synchronization testing
**Hardware**: Arduino MKR WAN 1310 with RTC module
**Features**:
- Clock accuracy validation
- Timestamp synchronization testing
- Long-term drift measurement

## Usage Guidelines

### Pre-Deployment Testing Sequence

1. **Basic Communication**
   ```bash
   # Upload Sender.ino to device A
   # Upload Receiver.ino to device B
   # Verify packet reception at various distances
   ```

2. **Protocol Validation**
   ```bash
   # Upload Sensor_Lora.ino to sensor device
   # Upload Relay_Lora.ino to relay device
   # Test three-way handshake protocol
   ```

3. **Power Management**
   ```bash
   # Upload testArduinoLowPower.ino
   # Measure current consumption in all modes
   # Validate sleep/wake cycles
   ```

4. **Network Integration**
   ```bash
   # Upload testArduinoLoRaWAN.ino
   # Configure gateway credentials
   # Test end-to-end connectivity
   ```

### Test Environment Setup

#### **Laboratory Testing**
- Controlled RF environment
- Calibrated power measurement equipment
- Multiple Arduino devices for protocol testing
- LoRaWAN gateway access for integration testing

#### **Field Testing**
- Realistic deployment conditions
- Range testing in actual environment
- Environmental stress testing
- Long-term reliability validation

### Expected Test Results

#### **Communication Range**
- **LoRa (Sensor-Relay)**: 50-100m underwater, 1-3km surface
- **LoRaWAN (Relay-Gateway)**: 2-10km depending on terrain
- **Packet Success Rate**: >95% under normal conditions

#### **Power Consumption**
- **Active Mode**: 50-120mA during communication
- **Sleep Mode**: <0.1mA continuous
- **Battery Life**: 8-12 months for typical sensor deployment

#### **Timing Accuracy**
- **RTC Drift**: <1 minute per month
- **Measurement Intervals**: ±30 seconds precision
- **Synchronization**: <5 second variance across network

## Integration with CI/CD

These tests are integrated into the automated validation workflows:

```yaml
# Hardware validation pipeline
- Arduino compilation testing
- Protocol communication validation  
- Power consumption verification
- Range and reliability testing
```

## Troubleshooting Common Issues

### **Communication Failures**
- Check antenna connections and positioning
- Verify frequency settings (868MHz EU, 915MHz US)
- Validate device addresses and protocol configuration

### **Power Issues**
- Measure actual vs. expected current consumption
- Check deep sleep mode engagement
- Verify RTC wake-up functionality

### **Range Problems**
- Test line-of-sight vs. obstructed scenarios
- Check underwater signal propagation
- Validate antenna design and placement

## Related Documentation

- [LoRa Protocol Specification](../protocols/lora-protocol.md)
- [Power Management Guide](../docs/power-management.md)
- [Field Testing Procedures](../deployment/testing-procedures.md)
- [CI/CD Integration](../../.github/workflows/hardware-validation.yml)