**Sensor – River Bed Monitoring System (MOLONARI 1D)**
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

This code implements the complete workflow of a MOLONARI field node:
Read configuration from an SD-stored CSV file (config_sensor.csv)
Initialize all connected sensors dynamically
Acquire and log temperature/pressure data locally
Transmit data via LoRa at defined intervals (with retry mechanism)
Enter low-power sleep until the next measurement cycle


*Hardware Requirements*

Component	Description
Arduino MKR WAN 1310	Main controller with LoRa radio
FeatherWing Adalogger	SD card slot for local data backup
Temperature sensors	DS18B20 or equivalent (waterproof)
Pressure sensors	Differential/absolute sensors for water depth
LoRa antenna	Long-range communication
Power source	3.7 V Li-ion battery (≥ 5000 mAh recommended)


*Core Functionalities*


Multi-sensor temperature and pressure acquisition
Dynamic configuration via CSV file
Local SD logging (RECORDS.CSV)
LoRa transmission with retry and recovery
Catch-up mechanism when transmission fails
Deep sleep between measurements for long autonomy


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
Header	Description
Measure.hpp	Sensor class and measurement routines
Writer.hpp	SD logging and CSV management
LoRa_Molonari.hpp	Custom LoRa communication protocol
Time.hpp	Time and RTC utilities
Waiter.hpp	Sleep and wake-up control
Reader.hpp	Configuration file parser


*Configuration File (config_sensor.csv)*
Example:


# --- Sensors ---
TEMP1,temperature,A0,BOX001
PRESS1,pressure,4,BOX001
Each line defines a sensor with:
id,type_capteur,pin,id_box
Analog pins may use the “A” prefix (e.g., A0 → Arduino A0 input).

⚠️ Warning: Any modification to config_sensor.csv requires corresponding updates to:
the lireConfigCSV function in Reader.cpp,
the StructConfig structure in Reader.hpp,
the Sensor class (both public and private members) in Measure.hpp,
the Sensor constructor in Measure.cpp,
and the sensor initialization section in the setup() function of main.cpp.


🔧 Code Structure
Global Variables
Sensor** sens;
double* toute_mesure;
Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";
LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE);
unsigned long lastLoRaSend = 0;
unsigned long lastSDOffset = 0;
std::queue<String> sendQueue;
Variable	Description
sens	Array of dynamically allocated sensor objects
toute_mesure	Last measurement values
logger	Handles SD writing
lora	Manages LoRa communication
lastLoRaSend	Timestamp of last successful LoRa send
lastSDOffset	Byte offset in SD file for catch-up transmission
⚙️ setup() — Initialization Phase
Initialize LED & Serial
pinMode(LED_BUILTIN, OUTPUT);
digitalWrite(LED_BUILTIN, HIGH);
Serial.begin(115200);
Load Configuration
Reader reader;
reader.lireConfigCSV("config_sensor.csv");
→ Populates liste_capteurs from the CSV file.
Allocate and Initialize Sensors
sens = new Sensor*[ncapteur];
toute_mesure = new double[ncapteur];
for (const auto& _c : liste_capteurs) {
    sens[it] = new Sensor(_c.pin, 1, 0.0, 1.0, _c.type_capteur, _c.id);
}
Initialize SD, Logger, and RTC
SD.begin(CSPin);
logger.EstablishConnection(CSPin);
InitialiseRTC();
Enter standby (LED off)


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


*LoRa Communication*
Custom MOLONARI protocol (defined in LoRa_Molonari.hpp)
Each payload sent through lora.sendPackets()
Up to 3 retries per line, acknowledgment-based reliability
Resumes from lastSDOffset after interruption


*Power Management*
Mode	Current	Duration	Description
Active Measurement	~50 mA	30 s	Sensors powered and read
LoRa Transmission	~120 mA	5 s	Data upload
Deep Sleep	<0.1 mA	Continuous	Waiting for next cycle
→ Estimated autonomy: 8–12 months on a 5000 mAh Li-ion battery.


*Testing & Deployment*
Prepare hardware (MKR WAN 1310 + sensors + SD module).
Copy config_sensor.csv to SD card.
Upload firmware via PlatformIO or Arduino IDE.
Open Serial Monitor @ 115200 baud to view logs.
Verify measurements in RECORDS.CSV.
Deploy sensor node in waterproof housing.

*Developer Notes*
Modular structure allows individual testing of subsystems.
Configuration-driven design → easy field updates.
Extendible with new sensor types (pH, turbidity, etc.).
Ready for multi-node LoRa networks (MASTER / SLAVE roles).


*Related Documentation*
LoRa Protocol (MOLONARI)
Hardware Assembly Guide
Deployment Procedures
Power Management Notes


*Summary*
This firmware now reflects the updated Reader-based dynamic configuration, the MOLONARI LoRa module, and the refined sleep/transmission cycle.
It provides a reliable, low-power, and field-ready framework for autonomous river bed monitoring.