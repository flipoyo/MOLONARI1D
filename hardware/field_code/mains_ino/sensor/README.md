# **Sensor – River Bed Monitoring System (MOLONARI 1D)**
This firmware is part of the MOLONARI 1D project, designed for river bed monitoring using temperature and pressure sensors connected to an Arduino MKR WAN 1310.
It combines LoRa communication, SD card logging, and low-power management for long-term autonomous operation.


# Configuration 

Tableau des capteurs avec id, type, pin et id_box

Puis configuration générale avec : 
- intervalle_de_mesure_secondes
- intervalle_lora_secondes
- pas de intervalle_lorawan_secondes parce que on envoie dès que on recoit car c'est plus simple à gérer dans l'optique de mettre plusieurs boitiers
- max_pload_octet
- periode_lora_min_secondes
- periode_mesure_min_secondes : intervalle_de_mesure_secondes doit être plus grand que nombre_capteur*periode_min_secondes
- max_secondes_par_jour : ca c'est la loi

Les limitations sont prises TRES LARGES.

Tout n'est pas utilisé dans le code mais ca nous permet d'avoir un fichier main.cpp mais ca nous permet d'avoir un fichier commun avec le groupe qui s'occupe de la gateway et du serveur.

*Overview*

## Summary 
This code implements the complete workflow of an arduino used ofr the sensor.

It :
- Reads the configuration of the csv file
- Measures data periodicaly
- Stores it on the SD card and sends it to the relay
- Listen to informations from the relay to modify the csv file if necessary


## *Hardware Requirements*

Component	Description
Arduino MKR WAN 1310	Main controller with LoRa radio
FeatherWing Adalogger	SD card slot for local data backup
Temperature sensors	DS18B20 or equivalent (waterproof)
Pressure sensors	Differential/absolute sensors for water depth
LoRa antenna	Long-range communication
Power source	3.7 V Li-ion battery (≥ 5000 mAh recommended)


## *Core Functionalities*


- Multi-sensor temperature and pressure acquisition
- Dynamic configuration via CSV file
- Local SD logging
- LoRa transmission with retry and recovery
- Catch-up mechanism when transmission fails
- Deep sleep between measurements for long autonomy
- Reconfiguration of CSV file


*Libraries Used*
#include <queue>
#include <vector>
#include <Arduino.h>
#include <SD.h>
#include <LoRa.h>
#include <ArduinoLowPower.h>

#include "Measure.hpp"
#include "Writer.hpp"
#include "LoRa_Molonari.hpp"
#include "Time.hpp"
#include "Waiter.hpp"
#include "Reader.hpp"


## Sensors
Each line of the CSV file defines a sensor with:
id,type_capteur,pin,id_box


⚠️ Warning: Any modification to config_sensor.csv requires corresponding updates to:
the lireConfigCSV function in Reader.cpp,
the StructConfig structure in Reader.hpp,
the Sensor class (both public and private members) in Measure.hpp,
the Sensor constructor in Measure.cpp,
and the sensor initialization section in the setup() function of main.cpp. ⚠️ 


## Code Structure


*loop() — Measurement & Transmission Cycle*
1. Take Measurements
for (auto &c : liste_capteurs) {
    toute_mesure[ncapt] = sens[ncapt]->Measure();
}
2. Log Data
logger.LogData(ncapt, toute_mesure);
3. LoRa Transmission
Checks if interval elapsed:
bool IsTimeToLoRa = (current_Time - lastLoRaSend >= config.intervalle_lora_secondes);
Reads unsent lines from SD, sends each via LoRa with 3 retries (20 s apart).
4. Catch-up Recovery
If previous transmissions failed, rattrapage = true ensures data continuity.
5. Sleep
Waiter waiter;
waiter.sleepUntil(CalculateSleepTimeUntilNextMeasurement());



*Testing & Deployment*
Prepare hardware (MKR WAN 1310 + sensors + SD module).
Copy config_sensor.csv to SD card.
Upload firmware via PlatformIO.
Open Serial Monitor @ 115200 baud to view logs.
Verify measurements in RECORDS.CSV.
Deploy sensor.
