# Device Communication Module

This directory contains the Python emulation of the LoRa communication protocol used between Arduino sensors and relays in the MOLONARI project.

## Quick Start

```bash
# Install dependencies
cd communication/
pip install -r requirements.txt

# Run demonstration
python examples/demo.py

# Test full communication (requires MQTT broker)
python examples/relay_emulator.py    # Terminal 1
python examples/sensor_emulator.py   # Terminal 2
```

## Contents

- **`communication/`** - Python LoRa protocol emulation over MQTT
- **`hardwareProgramming/`** - Original Arduino LoRa implementation
- **`hardware/`** - Physical device specifications
- **`installationSystem/`** - Deployment instructions

## Key Features

The Python emulation maintains full compatibility with the Arduino LoRa protocol:
- Same packet structure and checksum calculation
- Same request types (SYN/ACK/DATA/FIN) and addresses
- Same 3-way handshake and retry mechanisms
- MQTT transport layer replaces LoRa radio

For detailed documentation, see `communication/README.md`.