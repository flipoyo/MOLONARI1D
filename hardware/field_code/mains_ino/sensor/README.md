# **Sensor – River Bed Monitoring System (MOLONARI 1D)**
This firmware is part of the MOLONARI 1D project, designed for river bed monitoring using temperature and pressure sensors connected to an Arduino MKR WAN 1310. Read the README.md in harware first !
It combines LoRa communication, SD card logging, and low-power management for long-term autonomous measurements and transfer.



## Summary 
This code implements the complete workflow of an arduino used ofr the sensor.

It :
- Reads the configuration of the csv file
- Measures data periodicaly
- Stores it on the SD card and sends it to the relay


## *Core Functionalities*


- Multi-sensor temperature and pressure acquisition
- Dynamic configuration via CSV file
- Local SD logging
- LoRa transmission with retry and recovery
- Catch-up mechanism when transmission fails
- Deep sleep between measurements for long autonomy
- Reconfiguration of CSV file


*Libraries Used* : 

- queue
- vector
- Arduino.h
- SD.h
- LoRa.h
- ArduinoLowPower.h

- "LoRa_Molonari.hpp"
- "Measure.hpp"
- "Reader.hpp"
- "Time.hpp"
- "Waiter.hpp"
- "Writer.hpp"


## Sensors
Each line of the CSV file defines a sensor with:
id,type_capteur,pin,id_box


⚠️ Warning: Any modification to the structure of conf.csv requires corresponding updates to:
the lireConfigCSV function in Reader.cpp,
the StructConfig structure in Reader.hpp,
the Sensor class (both public and private members) in Measure.hpp,
the Sensor constructor in Measure.cpp,
and the sensor initialization section in the setup() function of main.cpp. ⚠️ 


## Code Structure

2. Main Loop (loop)
The main loop performs the following operations:

a) Measurement
- Checks whether the time since the last measurement exceeds intervalle_de_mesure_secondes.
- Reads all connected sensors and stores their readings in the toute_mesure vector.

b) SD Storage
- Logs all measurements into the RECORDS.CSV file using the logger object.

c) LoRa Transmission
- Checks if the LoRa transmission interval has been reached.
-Sends the stored measurements from the SD card to the LoRa master device.
- Retries up to 3 times if the transmission fails.
- Updates the SD file position (lastSDOffset) to prevent duplicate transmissions.
- Checks for incoming configuration updates from the LoRa master.

d) Sleep Management
- Calculates the time remaining until the next measurement or LoRa communication.
- Puts the Arduino into sleep mode using Waiter.sleepUntil() to save energy.

## Configuration : using this particular code (for the general method see the README in hardware)

### Filling conf.csv

a) You can change the intervals used for measurement and sending but it's porbably unnecessary.

b) Do not modify the second paragraph.

c) Change sensor configuration for it to match the pins oon your arduino.

d) 
