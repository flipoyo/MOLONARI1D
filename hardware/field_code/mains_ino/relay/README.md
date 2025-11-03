# **Relay – Data Forwarding Node (MOLONARI 1D)**

This firmware is part of the **MOLONARI 1D** project, acting as the **relay unit** between a sensor node and the gateway.
It ensures reliable data forwarding, configuration management, and low-power operation.

Before using this code, please read the README.md in the hardware section to understand the overall system architecture.

---

## Summary

This code implements the complete workflow of the **relay node** in the MOLONARI 1D system.

It:
- Reads configuration parameters from a CSV file stored on the SD card.  
- Establishes LoRa communication with sensor nodes (slaves).
- Forwards data packets via LoRaWAN.  
- Operates in low-power mode between transmissions.

---

## *Core Functionalities*

- LoRa receiver for communication with multiple sensor nodes.  
- Forwarding of received packets to a LoRaWAN network.  
- Dynamic configuration via CSV file (`conf_rel.csv`).  
- SD card management for configuration storage and updates.  
- Retry mechanisms for robust data transmission.  
- Downlink configuration updates via LoRaWAN.  
- Low-power idle mode between communication windows.

**Libraries Used:**

- `Arduino.h`  
- `SD.h`  
- `queue`  
- `ArduinoLowPower.h`  
- `MKRWAN.h`  

- `"LoRaWan_Molonari.hpp"`  
- `"LoRa_Molonari.hpp"`  
- `"Waiter.hpp"`  
- `"Reader.hpp"`  
- `"Time.hpp"`

---


## Code Structure

### 1. Setup (`setup`)

The setup routine:
- Initializes serial communication and the built-in LED.  
- Reads configuration data from `conf.csv` on the SD card.  
- Initializes LoRa and LoRaWAN communication parameters.  
- Checks SD card availability and halts if missing.  
- Prints system status messages for debugging.

### 2. Main Loop (`loop`)

The loop performs the following operations:

#### a) LoRa Reception
- Waits until the configured LoRa interval (`lora_intervalle_secondes`) is reached.  
- Initiates a handshake with sensor nodes.  
- Receives data packets and closes the LoRa session.  
- Stores received packets in a sending queue.


#### b) LoRaWAN Transmission
- Establishes a LoRaWAN session using `appEui` and `devEui`.  
- Sends all queued packets to the LoRaWAN network.  
- Retries automatically if some packets fail.  
- Reports transmission success or failure via Serial output.


#### c) Low-Power Management
- Calculates the remaining time before the next communication window.  
- Puts the Arduino into **idle low-power mode** using `LowPower.idle()`.

---

## Configuration and using this code

### Filling conf.csv

a) You can change the intervals used for measurement and sending but it's porbably unnecessary.

b) Do not modify the second paragraph.

c) Change sensor configuration for it to match the pins oon your arduino.

d) 

### Using the code

- Upload the code on the arduino via platformio. 
- Put the conf.csv in the SD card, that goes in the arduino.
- You're set up !

