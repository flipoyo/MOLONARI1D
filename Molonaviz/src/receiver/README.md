# Molonari Receiver

## Overview
The Molonari Receiver is designed to handle data from IoT devices using MQTT protocol. It processes incoming messages, decodes them, and stores the relevant information in a local SQLite database. The project also provides functionality for exporting data to CSV format for analysis, and ultimately store it in the Molonaviz database (`Molonaviz/TestDatabase/Molonari/Molonari.sqlite` of which the architecture is detailed in `Molonaviz/src/molonaviz/doc`).
This part is the final step of the Molonari transmission chain. It enables the user to receive the data sent through the network (device → relay → gateway), decode the datapayload, and put it in the DB.
The server setup is available in `hardware/specs`.


## Project Structure
```
Molonaviz
├── src
│   ├── receiver
│   │   ├── settings
│   │   │   ├── CA.crt             # Certification Authority certificate
│   │   │   ├── TLS.crt            # TLS configuration certificate
│   │   │   ├── TLS.key            # TLS configuration key
│   │   │   └── config.json        # MQTT broker and database configuration
│   │   ├── __init__.py
│   │   ├── main.py                # Entry point of the application
│   │   ├── adapt_nodered_mqtt.py  # Handles MQTT connection and message processing
│   │   ├── db_insertion.py        # Manages data insertion into the database
│   │   ├── decoder.py             # Decodes base64-encoded Protobuf messages
│   │   ├── GUI_virtual_lab.py     # Interface to create the virtual lab objects, in order to fill information in the DB
│   │   ├── logger_timestamps.py   # Logs timestamps from devices, relays and gateways
│   │   ├── timestamps.log         # Log record for devices, relays and gateways timestamps
│   │   ├── sensor_pb2.py          # Generated Protobuf message structure
│   │   └── README.md              # Project documentation
```

## Setup Instructions
1. **Install dependencies**:  
   Ensure you have these modules installed on your machine:
   ```paho.mqtt
   PyQt5.QtSql
   threading
   logging
   tkinter
   ```

2. **Configuration**:  
   Modify the `src/receiver/settings/config.json` file to set your desired configuration constants.

   **Important:**
   To be able to get MQTT configuration constants (broker, topic...), please go to `hardware/specs/XXX` to get started with Chirpstack configuration (connecting to the server, adding a device, generating certificates and an application...)

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