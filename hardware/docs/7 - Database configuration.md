# Database Configuration

## Adding Devices to the Database

Once your devices are ready to operate, you need to add them to the database. To add your devices, run the script `src.receiver.GUI_labo_virtuel`.

### Adding a Laboratory and a Study

If you are the first user from your laboratory to use the MOLONARI system, you need to create a new Laboratory (Labo), which will contain all devices from your institution.

1. Click the "Add Labo" button and select your name. All your devices will be listed under this name.
2. Then, create a new Study, which represents the location where you want to deploy devices for an experiment.

### Adding Your Devices (Order and Details)

You must add your devices in a specific order to satisfy database foreign key (FK) constraints:

1. **Gateway**

   * The starting point of your network.
   * Ensure you have the Gateway EUI (see Readme 5 - Gateway and server configuration, step 4). This ID must match the one registered on ChirpStack.
   * For the fields `TLS_Cert`, `TLS_Key`, and `CA_Cert`, enter the paths (or the content if storing certificates directly) to the certificates you generated to secure communication (see Readme 5).

2. **Relay**

   * The relay extends the Gateway's range.
   * To add a Relay, select a Gateway from those already registered in your lab using the dropdown menu. Make sure to link the relay to the physically deployed Gateway.

3. **Datalogger**

   * Represents the LoRaWAN chip embedded in the measurement device.
   * The `DevEUI` field corresponds to the unique chip identifier, usually found on the device box.
   * You must select the Relay this device will be associated with on the network.

4. **Thermometer and PressureSensor (Sensor Models)**

   * These tables define sensor models and their physical properties, necessary for calibration.
   * **Thermometer**: Enter the model name and the physical parameters of your thermistor. The `Beta` and `V` fields are critical for MOLONARI's Volt → Temperature calibration (used in real-time conversion).
   * **PressureSensor**: Enter the calibration coefficients for pressure (`Intercept`, `DuDH`, `DuDT`) and the thermometer model (`ThermoModel`) used for thermal compensation of pressure measurements.

5. **Shaft and SamplingPoint (Physical Link)**

   * Final step linking device models to physical locations and experimental parameters.
   * **Shaft**: Defines the physical soil column. Set the actual depths (`Depth1` to `Depth4`) where sensors are placed. The `ThermoModel` field links the Shaft to the thermometer model used for all temperature measurements in this column.
   * **SamplingPoint**: Represents the experimental measurement point. Link it to the physical column (`Shaft`), the pressure sensor (`PressureSensor`), and the associated study (`Study`). Fields like `Offset` (sensor height) and `RiverBed` (riverbed height) are essential for calculations.

Following this order ensures that the database is correctly initialized and ready to receive and process real-time MQTT data.
