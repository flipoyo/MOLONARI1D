# Molonari Receiver

## Overview
The Molonari Receiver project is designed to handle data from IoT devices using MQTT protocol. It processes incoming messages, decodes them, and stores the relevant information in a local SQLite database. The project also provides functionality for exporting data to CSV format for analysis.

**To be noted**: to this stage, the local system is not implemented inside of the Molonaviz interface. Its mission is to provide a first setup to inscribe datapayloads in a DB, in order to be displayed then computed.

## Project Structure
```
Molonaviz
├── src
│   ├── receiver
│   │   ├── main.py                # Entry point of the application
│   │   ├── config.json            # Configuration constants in JSON format
│   │   ├── adapt_nodered_mqtt.py  # Handles MQTT connection and message processing
│   │   ├── decoder.py             # Decodes base64-encoded Protobuf messages
│   │   ├── db_insertion.py        # Manages data insertion into the database
│   │   ├── logger_timestamps.py   # Logs timestamps from devices, relays and gateways
│   │   ├── timestamps.log         # Log record for devices, relays and gateways timestamps
│   │   ├── sensor_pb2.py          # Generated Protobuf message structure
│   ├── README.md                  # Project documentation
│   └── requirements.txt           # Project dependencies
└── tests
    └── test_config.py             # Unit tests for configuration loading and validation
```

## Setup Instructions
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd molonari-receiver
   ```

2. **Install dependencies**:
   Ensure you have Python 3.x installed. Then, install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**:
   Modify the `src/receiver/config.json` file to set your desired configuration constants.

4. **Running the Application**:
   To start the application, run:
   ```bash
   python src/receiver/main.py
   ```
   To export the database to a CSV file, use:
   ```bash
   python src/receiver/main.py --export output.csv
   ```

## Usage
The application connects to an MQTT broker, listens for messages, decodes them, and stores the relevant data in a SQLite database. It also logs timestamps for various events (device upload, relay and gateway processings), which can be useful for debugging and analysis.

## Testing
Unit tests are provided in the `src/tests/test_config.py` file. You can run the tests using:
```bash
pytest src/tests
```