 Sensor - River Bed Monitoring System

This firmware is part of the **MOLONARI1D** project, designed for **river bed monitoring** through **temperature** and **pressure sensors** connected to an **Arduino MKR WAN 1310**.  
It combines **LoRa transmission**, **SD card logging**, and **low-power management** for long-term autonomous operation.

---

## Overview

This demonstration code showcases the full sensor workflow — from measurement to data transmission — in realistic field-like conditions.  
It allows developers to test, calibrate, and validate the MOLONARI sensor nodes before underwater deployment.

---

## Hardware Requirements

| Component | Description |
|------------|-------------|
| **Arduino MKR WAN 1310** | Main microcontroller (LoRa compatible) |
| **Featherwing Adalogger** | SD card module for data backup |
| **Temperature sensors** | DS18B20 or equivalent (waterproof) |
| **Pressure sensors** | Differential pressure sensors |
| **LoRa antenna** | For communication with relay stations |

---

## Functionalities

- Multi-sensor **temperature** and **pressure** acquisition  
- **Local SD logging** in CSV format  
- **LoRa transmission** with retry and acknowledgment  
- **Power-efficient sleep** between measurements  
- **Catch-up mechanism** in case of LoRa communication loss  


---

## Configuration

- Enables setting the type and position of each sensor connected to the Arduino. 
- Enables setting the interval between measurements.
- Enables setting the interval between sending throught LoRa.

## Code Explanation

### 1. Included Libraries

```cpp
#include <queue>
#include <vector>
#include <Arduino.h>
#include <SD.h>
#include <LoRa.h>
#include <ArduinoLowPower.h>
```

These are the **core libraries** for Arduino, SD card management, LoRa communication, and low-power functions.  
Custom headers (`Measure.hpp`, `Writer.hpp`, etc.) provide project-specific logic.

---

### 2. Global Variables

```cpp
Sensor** sens;
double *toute_mesure;
Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";
LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE);
```

| Variable | Role |
|-----------|------|
| `sens` | Array of sensor pointers (temperature/pressure) |
| `toute_mesure` | Stores the most recent measurement values |
| `logger` | Handles SD card writing |
| `CSPin` | Chip Select pin for SD card |
| `lora` | Manages LoRa communication on **868 MHz** as a **slave node** |

---

### 3. `setup()` — Initialization Phase

```cpp
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.begin(115200);
```
- Turns on the LED during initialization.  
- Starts serial communication for debugging.

#### Configuration File Reading

```cpp
Reader reader;
reader.lireConfigCSV("config_sensor.csv");
```
Reads configuration file (`config_sensor.csv`) that defines:
- Number and type of sensors  
- Pin assignments  
- Calibration parameters (offset, scale)

#### Sensor Allocation

```cpp
sens = new Sensor*[ncapteur];
toute_mesure = new double[ncapteur];
```
Allocates memory for each sensor and its measurements.

#### SD and RTC Initialization

```cpp
SD.begin(CSPin);
logger.EstablishConnection(CSPin);
InitialiseRTC();
```
Initializes SD card logging and the real-time clock.  
Finally, the LED is turned off to save power.

---

### 4. `loop()` — Measurement and Transmission Cycle

Each loop iteration corresponds to one **measurement cycle**.

#### a. Sensor Measurements

```cpp
for (auto &c : liste_capteurs) {
    toute_mesure[ncapt] = sens[ncapt]->Measure();
}
```
All sensors take their measurements and store the results in `toute_mesure`.

#### b. Store on SD Card

```cpp
logger.LogData(ncapt, toute_mesure);
```
Writes all current measurements to `RECORDS.CSV` with timestamps and CSV formatting.

#### c. LoRa Transmission

```cpp
unsigned long current_Time = GetSecondsSinceMidnight();
int LORA_INTERVAL_S = config.intervalle_lora_secondes;
bool IsTimeToLoRa = (current_Time - lastLoRaSend >= LORA_INTERVAL_S);
```
If the LoRa interval has elapsed or if **catch-up mode** (`rattrapage`) is active, the node attempts transmission.

```cpp
lora.startLoRa();
File dataFile = SD.open(filename, FILE_READ);
dataFile.seek(lastSDOffset);
```
The node resumes transmission from the last saved offset.  
Each line is sent up to **3 times**, with **20-second** delays if unsuccessful:

```cpp
for (int attempt = 1; attempt <= 3; attempt++) {
    if (lora.sendPackets(lineToSend)) {
        success = true;
        break;
    } else {
        delay(20000);
    }
}
```

If successful, the file offset is updated; otherwise, LoRa stops and retries later.

#### d. Deep Sleep Mode

```cpp
waiter.sleepUntil(CalculateSleepTimeUntilNextMeasurement());
```
The node enters deep sleep until the next scheduled measurement, minimizing power usage.

---

## LoRa Communication Protocol

- **Custom packet structure**: header, payload, checksum  
- **Acknowledgment-based reliability**  
- **Retry/timeout mechanism** (up to 3 attempts per packet)  
- **Role system** (`MASTER` / `SLAVE`) for two-way communication  

---

## Power Management

- LED disabled outside initialization  
- Uses `ArduinoLowPower` for deep sleep  
- Active only during:
  - Sensor measurement  
  - SD write  
  - LoRa transmission  

| Mode | Current | Duration | Frequency | Description |
|------|----------|-----------|------------|--------------|
| **Active Measurement** | ~50 mA | 30 s | Every 15 min | Sensor reading |
| **LoRa Transmission** | ~120 mA | 5 s | Once per day | Data upload |
| **Deep Sleep** | <0.1 mA | Continuous | — | Standby mode |

**Estimated battery life:** 8–12 months (5000 mAh Li-ion)

---

## Testing & Deployment

1. Connect Arduino MKR WAN 1310 with sensors and SD module.  
2. Upload the firmware via Arduino IDE.  
3. Open Serial Monitor (`115200 baud`) to check logs.  
4. Inspect `RECORDS.CSV` on the SD card.  
5. Deploy the node in a waterproof case.

---

## Developer Notes

- The modular structure (`internals/`) allows independent testing of each subsystem.  
- Future extensions can include:
  - New sensor types (pH, turbidity, conductivity)  
  - Adaptive transmission intervals based on water level  
  - Encryption layer for LoRa packets  

---

## Summary

This firmware demonstrates a **complete autonomous monitoring cycle**:
- Modular architecture  
- Reliable data handling and recovery  
- Power-efficient design  
- Ready for long-term field deployment in environmental monitoring

## Related Documentation

- [LoRa Protocol Specification](../../protocols/lora-protocol.md)
- [Hardware Assembly Guide](../../docs/assembly-guide.md)
- [Deployment Procedures](../../deployment/field-deployment.md)
- [Power Management](../../docs/power-management.md)