# LoRa Communication Protocol Emulation

This module provides a Python emulation of the LoRa communication protocol used between Arduino sensors and relays in the MOLONARI project. The emulation uses MQTT as the transport layer instead of actual LoRa radio communication, while maintaining the same packet structure and communication patterns as the original Arduino implementation.

## Overview

The original Arduino LoRa protocol is implemented in:
- `Device/hardwareProgramming/Tests Codes/Sensor_Lora/` - Sensor implementation
- `Device/hardwareProgramming/Tests Codes/Relay_Lora/` - Relay implementation

This Python emulation provides:
- **Same packet structure**: Checksum, Destination, Local Address, Packet Number, Request Type, Payload
- **Same communication flow**: 3-way handshake (SYN/SYN-ACK/ACK), data transmission with ACK, session closure (FIN)
- **Same request types**: SYN (0xcc), ACK (0x33), DATA (0xc3), FIN (0x3c)
- **Same retry mechanisms**: Up to 6 retries with exponential backoff
- **MQTT transport**: Uses MQTT broker instead of LoRa radio for message delivery

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have access to an MQTT broker (default: localhost:1883)

## Quick Start

### Simple Test
Run the basic test to verify functionality:
```bash
cd examples/
python simple_test.py
```

### Manual Sensor and Relay
Start the relay emulator in one terminal:
```bash
cd examples/
python relay_emulator.py
```

Start the sensor emulator in another terminal:
```bash
cd examples/
python sensor_emulator.py
```

## API Reference

### Core Classes

#### `LoRaCommunication`
Main class that emulates the Arduino LoRa communication protocol.

```python
from Device.communication import LoRaCommunication, RequestType

lora = LoRaCommunication(
    frequency=868e6,           # LoRa frequency (for compatibility)
    local_address=0xcc,        # This device's address
    destination=0xaa,          # Target device address
    mqtt_broker="localhost",   # MQTT broker hostname
    mqtt_port=1883,           # MQTT broker port
    debug=True                # Enable debug logging
)
```

#### `LoRaSensorEmulator`
High-level sensor emulation with simplified interface.

```python
from Device.communication.lora_emulation import LoRaSensorEmulator

sensor = LoRaSensorEmulator(
    local_address=0xcc,
    relay_address=0xaa,
    debug=True
)

# Send data in a complete session
data = ["message1", "message2", "message3"]
success = sensor.send_data_session(data)
```

#### `LoRaRelayEmulator`
High-level relay emulation with simplified interface.

```python
from Device.communication.lora_emulation import LoRaRelayEmulator

relay = LoRaRelayEmulator(
    local_address=0xaa,
    debug=True
)

# Receive data in a complete session
received_data = relay.receive_data_session(shift_back=0)
```

### Protocol Methods

#### Handshake
```python
# Sensor initiates handshake
success, shift = lora.perform_handshake_sensor()

# Relay responds to handshake
success = lora.perform_handshake_relay(shift_back=0)
```

#### Data Transmission
```python
# Sensor sends multiple packets
data_list = ["data1", "data2", "data3"]
last_packet = lora.send_packets(data_list)

# Relay receives multiple packets
receive_queue = []
last_packet = lora.receive_packets(receive_queue)
```

#### Session Management
```python
# Start/stop communication
lora.start_lora()
lora.stop_lora()

# Close session
lora.close_session(last_packet_number)
```

## Protocol Details

### Packet Structure
Each packet contains:
- **Checksum** (1 byte): XOR checksum for integrity
- **Destination** (1 byte): Target device address
- **Local Address** (1 byte): Sender device address  
- **Packet Number** (1 byte): Sequential packet counter
- **Request Type** (1 byte): SYN/ACK/DATA/FIN
- **Payload** (variable): Message content

### Communication Flow

1. **Handshake Phase**:
   - Sensor sends SYN packet
   - Relay responds with SYN-ACK (includes shift value)
   - Sensor confirms with ACK packet

2. **Data Transfer Phase**:
   - Sensor sends DATA packets sequentially
   - Relay acknowledges each packet with ACK
   - Retries up to 6 times if ACK not received

3. **Session Closure**:
   - Sensor sends FIN packet
   - Relay acknowledges with FIN packet
   - Session complete

### MQTT Topics
The emulation uses MQTT topics in the format:
```
molonari/lora/{frequency}MHz/device/{address}
```

For example:
- `molonari/lora/868MHz/device/aa` - Messages for relay (0xaa)
- `molonari/lora/868MHz/device/cc` - Messages for sensor (0xcc)

## Configuration

### MQTT Broker
The default configuration expects an MQTT broker on localhost:1883. You can change this:

```python
lora = LoRaCommunication(
    frequency=868e6,
    local_address=0xcc,
    destination=0xaa,
    mqtt_broker="your-mqtt-broker.com",
    mqtt_port=1883
)
```

### Device Addresses
Default addresses match the Arduino implementation:
- Relay: `0xaa`
- Sensors: `0xbb`, `0xcc` (authorized in relay's network)

### Logging
Enable debug logging to see detailed protocol messages:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See the `examples/` directory for complete working examples:

- `simple_test.py` - Basic functionality test
- `sensor_emulator.py` - Full sensor emulation (matches Arduino behavior)
- `relay_emulator.py` - Full relay emulation (matches Arduino behavior)

## Testing with MQTT Broker

### Using Mosquitto (Linux/Mac)
```bash
# Install mosquitto
sudo apt-get install mosquitto mosquitto-clients  # Ubuntu/Debian
brew install mosquitto                             # macOS

# Start broker
mosquitto

# Monitor messages (in another terminal)
mosquitto_sub -h localhost -t "molonari/lora/+/device/+"
```

### Using Docker
```bash
# Start MQTT broker in container
docker run -it -p 1883:1883 eclipse-mosquitto:latest

# Monitor messages
docker run --rm -it --network host eclipse-mosquitto:latest mosquitto_sub -h localhost -t "molonari/lora/+/device/+"
```

## Compatibility

This emulation maintains full compatibility with the Arduino LoRa protocol:
- Same packet format and field ordering
- Same checksum calculation (XOR)
- Same request types and values
- Same retry logic and timeouts
- Same handshake and session management

The only difference is the transport layer (MQTT instead of LoRa radio).

## Troubleshooting

### Connection Issues
- Ensure MQTT broker is running and accessible
- Check firewall settings for port 1883
- Verify network connectivity

### Protocol Issues
- Enable debug logging to see detailed message flow
- Check device addresses are configured correctly
- Verify MQTT topics are correctly formatted

### Performance
- MQTT introduces some latency compared to direct LoRa
- Adjust timeouts if experiencing packet loss
- Consider local MQTT broker for better performance