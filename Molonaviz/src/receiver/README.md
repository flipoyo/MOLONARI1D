# Molonari Receiver

## Overview
The Molonari Receiver is designed to handle data from IoT devices using MQTT protocol. It processes incoming messages, decodes them, and stores the relevant information in a local SQLite database. The project also provides functionality for exporting data to CSV format for analysis, and ultimately store it in the Molonaviz database.

**To be noted**: to this stage, the local system is not implemented inside of the Molonaviz interface. Its mission is to provide a first setup to inscribe datapayloads in a DB, in order to be displayed then computed.

## Project Structure
```
Molonaviz
├── src
│   ├── receiver
│   │   ├── settings
│   │   │   ├── CA.crt             # Certification Authority certificate
│   │   │   ├── TLS.crt            # TLS configuration certificate
│   │   │   ├── TLS.key            # TLS configuration key
│   │   │   ├── config.json        # Configuration of the MQTT broker and database
│   │   │   ├── ERD_structure.sql  # File to create the database
│   │   ├── __init__.py
│   │   ├── main.py                # Entry point of the application
│   │   ├── adapt_nodered_mqtt.py  # Handles MQTT connection and message processing
│   │   ├── decoder.py             # Decodes base64-encoded Protobuf messages
│   │   ├── db_insertion.py        # Manages data insertion into the database
│   │   ├── logger_timestamps.py   # Logs timestamps from devices, relays and gateways
│   │   ├── timestamps.log         # Log record for devices, relays and gateways timestamps
│   │   ├── sensor_pb2.py          # Generated Protobuf message structure
│   │   └── device_config.py       # 
│   ├── README.md                  # Project documentation
│   └── requirements.txt           # Project dependencies
└── tests
    └── test_config.py             # Unit tests for configuration loading and validation
```

## Setup Instructions
1. **Install dependencies**:  
   Ensure you have Python 3.x installed. Then, install the required packages using pip.
   Put your bash in the /Molonaviz (not molonaviz) folder and run:
   ```bash
   pip install -e .
   ```

2. **Configuration**:  
   Modify the `src/receiver/settings/config.json` file to set your desired configuration constants.

3. **Running the Application**:  
   To start the application, put your bash in the /Molonaviz folder and run:
   ```bash
   python -m src.receiver.main
   ```
   To export the database to a CSV file, use:
   ```bash
   python -m src.receiver.main --export output.csv
   ```

## Usage
The application connects to an MQTT broker, listens for messages, decodes them, and stores the relevant data in a SQLite database. It also logs timestamps for various events (device upload, relay and gateway processings), which can be useful for debugging and analysis.

If the database doesn't exist when the script is launched, it is automatically created by the script. If `real_database_insertion` is set to `true` in the config file, then it will be created based on the `.sql` file provided, else a fixed basic database described in `db_insertion.py` will be used.