# MOLONARI Hardware 

This directory contains all hardware-related documentation and code for the MOLONARI1D sensors network, organized for efficient collaboration between hardware developers, protocol engineers, and system integrators.

If you want to build a MOLONARI1D device, you can dive directly into the `specs/` folder. To have an overview of the complete MOLONARI1D device, please consult `specs/v2-2025/README__#Overview_hardware_Molonari_1D_v2.0`.

For all that is related to the codes, the firmware part, you can consult the `firmware/` folder. 

## Directory Structure

```
hardware/
├── firmware/ 
│   ├── libs/                           # Librairies handmade for the project
│   │    ├── encode/
│   │    ├── LoRa_Molonari/
│   │    ├── LoRaWan_Molonari/
│   │    ├── Measure/
│   │    ├── Memory_monitor/
│   │    ├── Reader/
│   │    ├── Time/
│   │    ├── Waiter/
│   │    └── Writer/
│   ├── mains_ino/                          # Main codes we use    
│   │    └── relay/
│   │    │   ├── main.cpp
│   │    │   ├── conf.csv
│   │    │   ├── Relay.ino
│   │    │   └── README
│   │    └── sensor/
│   │    │   ├── main.cpp
│   │    │   ├── conf.csv
│   │    │   ├──  README
│   │    │   └── sensor.ino
│   │    └── demo/
│   │        ├── demo_relay/
│   │        └── demo_sensor/
├── specs/                             # All the specifications to build the hardware
│   ├── v1-until-2024/                           
│   ├── v2-2025/                           # v2 of the MOLONARI1D device specifications (2025 edition)
│   │    ├── costs/
│   │    ├── electronic connexion/
│   │    ├── gateway/
│   │    ├── relay/
│   │    ├── sensors/
│   │        ├── box/
│   │        ├── differential pressure sensor/
│   │        └── shaft/
│   │        └── temperature sensor/
│   │    └──README__#Overview_hardware_Molonari_1D_v2.0     #overview of the complete MOLONARI1D device (with pictures)
├── tests/
│   ├── Adjust_RTC/ 
│   ├── Connection_test/ 
│   ├── testArduinoLoRaWAN/  
│   ├── testArduinoLowPower/ 
│   ├── Sender/
│   ├── Receiver/
│   └── ...                  
├── docs/                               # Hardware documentation
│   ├── 1 - Installation guide_ENG.md
│   ├── 3 - Sensor's hardware-ENG.md
│   ├── 4 - Our LoRa protocol_ENG.md
│   └── ...
├── Trash/     
├── archived/               
│   ├── Archive_2024/
│   ├── Archive_before/
│   └── ...
└── README.md
```