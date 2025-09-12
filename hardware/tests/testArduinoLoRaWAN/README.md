# LoRaWAN Connectivity Test

Comprehensive test for validating LoRaWAN connectivity and gateway integration for relay stations in the MOLONARI1D monitoring system.

## Purpose

Validates the relay station's ability to connect to LoRaWAN networks and transmit aggregated sensor data to internet-connected gateways.

## Hardware Requirements

- **Arduino MKR WAN 1310** with LoRaWAN capability
- **LoRaWAN antenna** - Appropriate for local frequency band
- **LoRaWAN gateway** access - For network connectivity testing
- **Valid LoRaWAN credentials** - DevEUI, AppEUI, AppKey

## Test Coverage

### Network Join Procedures
- OTAA (Over-The-Air Activation) validation
- Network credentials verification
- Gateway discovery and selection
- Join request/accept cycle testing

### Data Transmission
- Payload formatting and validation
- Confirmed vs. unconfirmed transmissions
- Downlink message handling
- Duty cycle compliance testing

### Network Quality Assessment
- Signal strength measurement (RSSI/SNR)
- Gateway response time analysis
- Packet delivery confirmation
- Network coverage validation

## Configuration Requirements

### Device Credentials
```cpp
// Configure these for your LoRaWAN network
String appEui = "YOUR_APP_EUI";
String appKey = "YOUR_APP_KEY";
String devEui = "YOUR_DEV_EUI";
```

### Regional Settings
- **EU868**: European frequency band
- **US915**: North American frequency band
- **AS923**: Asian Pacific frequency band

## Test Procedures

### Pre-Test Setup
1. Register device with LoRaWAN network server
2. Configure network credentials in firmware
3. Verify gateway coverage at test location
4. Prepare monitoring tools for network analysis

### Connectivity Testing
1. **Join Network**: Validate OTAA join procedure
2. **Send Data**: Test payload transmission
3. **Receive Downlink**: Verify bidirectional communication
4. **Quality Assessment**: Measure signal quality and reliability

### Performance Validation
- **Join Time**: Network joining latency
- **Transmission Success**: Packet delivery rate
- **Signal Quality**: RSSI/SNR measurements
- **Duty Cycle**: Regulatory compliance verification

## Expected Results

### Successful Operation
- Network join within 30 seconds
- >95% packet delivery rate
- RSSI > -120 dBm for reliable communication
- Duty cycle compliance (<1% EU868, <4% US915)

### Quality Metrics
- **Join Success Rate**: >99% under normal conditions
- **Transmission Latency**: <10 seconds for confirmed messages
- **Network Coverage**: Consistent connectivity across deployment area
- **Gateway Selection**: Automatic optimal gateway selection

## Integration with System

This test validates the final communication link in the MOLONARI1D data pipeline:

```
Sensors → Relay → LoRaWAN Gateway → Network Server → Application Server
```

## Troubleshooting

### Common Issues
- **Join Failures**: Check credentials and gateway coverage
- **Transmission Errors**: Verify payload format and duty cycle
- **Range Issues**: Test different antenna configurations
- **Network Congestion**: Monitor gateway capacity and timing

### Debug Features
- Serial output for real-time status monitoring
- LED indicators for join status and transmission
- Error code reporting for diagnostic purposes
- Network quality metrics logging

## Related Documentation

- [LoRaWAN Integration Guide](../../protocols/lorawan-integration.md)
- [Gateway Configuration](../../docs/gateway-setup.md)
- [Network Planning](../../docs/network-design.md)
- [Regulatory Compliance](../../docs/regulatory-requirements.md)