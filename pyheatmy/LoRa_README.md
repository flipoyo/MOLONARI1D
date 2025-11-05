# LoRa/LoRaWAN Emitter for MOLONARI1D

This module provides classes to simulate LoRa and LoRaWAN transmission behavior from sensor data stored in CSV files. It emulates the communication protocols used by the MOLONARI1D project's Arduino MKR WAN 1310 devices.

## Features

- **CSV Data Loading**: Load sensor data from CSV files with automatic timestamp and value column detection
- **LoRa Packet Structure**: Implements the exact packet format used in the MOLONARI1D project
- **Realistic Transmission Simulation**: Accounts for spreading factors, airtime calculations, and potential failures
- **Retry Mechanism**: Exponential backoff retry with configurable maximum attempts (matches Arduino code)
- **LoRaWAN Network Simulation**: Includes join procedures (OTAA), duty cycle compliance, and network features
- **Comprehensive Statistics**: Detailed transmission metrics and success rates
- **Configurable Parameters**: All LoRa parameters (SF, frequency, power) are configurable

## Classes

### LoRaEmitter

Basic LoRa emitter that simulates local LoRa communication between sensors and relays.

```python
from pyheatmy import LoRaEmitter, LoRaSpreadingFactor, LoRaFrequency

# Initialize emitter
emitter = LoRaEmitter(
    device_address=0x05,  # Sensor address
    spreading_factor=LoRaSpreadingFactor.SF7,
    frequency=LoRaFrequency.EU868,
    power=14,  # dBm
    max_retries=6,  # As per MOLONARI1D documentation
    verbose=True
)

# Emit data from CSV file
results = emitter.emit_csv_data(
    "sensor_data.csv",
    destination=0x01,  # Relay address
    transmission_interval=0.5  # seconds between transmissions
)

# Get statistics
stats = emitter.get_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")
```

### LoRaWANEmitter

Extended emitter with LoRaWAN network features including join procedures and duty cycle compliance.

```python
from pyheatmy import LoRaWANEmitter, LoRaSpreadingFactor

# Initialize LoRaWAN emitter
emitter = LoRaWANEmitter(
    device_address=0x10,
    app_eui="0000000000000000",
    app_key="387BC5DEF778168781DDE361D4407953",
    spreading_factor=LoRaSpreadingFactor.SF10,
    duty_cycle_limit=0.01,  # 1% duty cycle (EU regulation)
    verbose=True
)

# Join network and emit data
results = emitter.emit_csv_data_lorawan("sensor_data.csv")

# Check LoRaWAN-specific statistics
stats = emitter.get_statistics()
print(f"Join status: {'Joined' if stats['is_joined'] else 'Not joined'}")
print(f"Current duty cycle: {stats['current_duty_cycle']*100:.3f}%")
```

## Packet Structure

The implementation follows the exact packet structure used in MOLONARI1D:

| Field | Size | Description |
|-------|------|-------------|
| Checksum | 1 byte | Data integrity verification |
| Destination | 1 byte | Receiving device address |
| Local Address | 1 byte | Sending device address |
| Packet Number | 1 byte | Sequential packet number |
| Request Type | 1 byte | Type of request (0xc3 for data) |
| Payload | Variable | Sensor data (max ~200 bytes) |

Example payload format: `"2024-11-07,10:00:12,21.55,22.11,21.99,21.30,1013.25"`

## CSV Data Format

The emitter can automatically detect and process various CSV formats. Example supported formats:

### Temperature Sensor Data
```csv
Date Heure, GMT+01:00,Temp1,Temp2,Temp3,Temp4
07/12/16 11:00:00 AM,22.154,21.604,20.317,20.65
07/12/16 11:15:00 AM,26.5,27.038,23.737,21.819
```

### Pressure Sensor Data
```csv
timestamp,pressure,temperature
2024-01-01 12:00:00,1013.25,21.5
2024-01-01 12:15:00,1013.50,21.8
```

## Spreading Factors and Performance

The implementation includes all LoRa spreading factors with realistic performance characteristics:

| SF | Bitrate (bps) | Symbol Time (ms) | Range | Data Rate |
|----|---------------|------------------|-------|-----------|
| SF7 | 5469 | 109.38 | Short | Fast |
| SF8 | 3125 | 219.77 | Medium | Medium |
| SF9 | 1758 | 439.45 | Medium | Medium |
| SF10 | 977 | 878.91 | Long | Slow |
| SF11 | 488 | 1757.81 | Long | Slow |
| SF12 | 244 | 3515.63 | Very Long | Very Slow |

## Usage Examples

### Basic LoRa Emission

```python
import pandas as pd
from pyheatmy import LoRaEmitter

# Create sample data
data = pd.DataFrame({
    'timestamp': ['2024-01-01 12:00:00', '2024-01-01 12:15:00'],
    'temperature': [21.5, 22.1],
    'pressure': [1013.2, 1013.5]
})
data.to_csv('sample_data.csv', index=False)

# Initialize and emit
emitter = LoRaEmitter(device_address=5)
results = emitter.emit_csv_data('sample_data.csv')

print(f"Transmitted {len(results)} packets")
print(f"Success rate: {emitter.get_success_rate():.1%}")
```

### LoRaWAN with Join Procedure

```python
from pyheatmy import LoRaWANEmitter

emitter = LoRaWANEmitter(
    device_address=10,
    app_eui="0000000000000000", 
    app_key="387BC5DEF778168781DDE361D4407953"
)

# Join network
if emitter.join_network():
    print("Successfully joined LoRaWAN network!")
    
    # Emit data
    results = emitter.emit_csv_data_lorawan('sensor_data.csv')
    
    # Check duty cycle compliance
    stats = emitter.get_statistics()
    print(f"Duty cycle usage: {stats['current_duty_cycle']*100:.3f}%")
```

## Testing

Run the comprehensive test suite:

```bash
cd pyheatmy
python -m pytest tests/test_lora_emitter.py -v
```

Run the example demonstration:

```bash
python example_lora_usage.py
```

## Integration with MOLONARI1D

This implementation is designed to integrate seamlessly with existing MOLONARI1D workflows:

```python
import pyheatmy

# Load sensor data using existing pyheatmy functionality
column = pyheatmy.Column(...)  # Your existing column setup

# Create LoRa emitter for data transmission simulation
emitter = pyheatmy.LoRaEmitter(device_address=5)

# Emit processed data
results = emitter.emit_csv_data('processed_sensor_data.csv')
```

## Hardware Compatibility

The implementation is based on the actual Arduino MKR WAN 1310 code used in MOLONARI1D:

- **Packet Structure**: Matches Arduino implementation exactly
- **Retry Logic**: Same 6-retry limit with exponential backoff
- **Timing**: Realistic airtime calculations based on LoRa specifications  
- **LoRaWAN Features**: OTAA join procedure, duty cycle compliance
- **Data Format**: Compatible with sensor data formats used in field deployments

## Future Enhancements

Potential areas for extension:

- **Network Topology Simulation**: Support for tree topology with multiple relays
- **Signal Propagation Models**: More sophisticated path loss and interference modeling
- **Real Hardware Interface**: Direct integration with actual LoRa modules
- **Advanced Scheduling**: Implementation of the scheduling algorithms described in documentation
- **Flood Recovery**: Simulation of extended outage scenarios and recovery procedures

## References

This implementation is based on the MOLONARI1D project documentation:
- `Device/hardwareProgramming/Documentation/4 - Our LoRa protocol_ENG.md`
- `Device/hardwareProgramming/Tests Codes/testArduinoLoRaWAN/`
- Arduino MKR WAN 1310 LoRa communication protocols