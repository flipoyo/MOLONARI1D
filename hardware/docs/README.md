MOLONARI 2024 : Mohammad Kassem, Zehan Huang, Lucas Brandi, Haidar Yousef, Valeria Vega Valenzuela

# Hardware Programming

This project focuses on the Molonari system, an environmental monitoring solution that integrates temperature and pressure sensors, data storage, and transmission via LoRa. Key components include the Adjust RTC for clock calibration, Relay/Relay_LoraWan for communication, and the Sensor module for data collection, storage in CSV format, and transmission. The system is designed for low power consumption to ensure efficient long-term operation. Sensor_demo serves as a simplified version for testing and presentation, while earlier code contributions in Archive_before form the foundational work for the project.

## Archive_before

This file contains the functional modules and code contributions developed by students in 2022 and 2023, serving as the early foundation for the project's hardware programming, which were modified in 2024.

## Documentation

The `Documentation` folder contains all the necessary files to understand and use the system. It includes detailed guides and technical references. Below is an overview of its main content:

### Installation Guide: 
The Installation Guide provides a comprehensive step-by-step tutorial for setting up and configuring the MOLONARI sensor system. It covers the following aspects:
* Prerequisites: A list of required hardware components (e.g., Arduino MKR WAN 1310, sensors, SD card module) and software tools (Arduino IDE, libraries).
* Electrical Connections: Detailed wiring instructions, including sensor integration and SD card module setup, with references to pin mappings.
* Code Setup: Instructions for uploading code to the sensor and relay boards, ensuring compatibility between hardware and software configurations.
* Power Management: Guidelines for optimizing energy efficiency, such as powering sensors only during measurement cycles.
* Final Assembly: Steps to assemble and secure the system for deployment, including sealing electronics in waterproof casings.
* Troubleshooting: A dedicated section addressing common issues, including SD card malfunctions, connection errors, and debugging using serial communication.

### Explaining the Sensor code:
This document explains the main sensor system code developed by the MOLONARI team, detailing its structure and functionality. It describes the main .ino file, which manages the system's workflow, along with the associated classes for measuring, recording, and transmitting temperature and pressure data. Additionally, it covers initialization, configuration, and operational logic in 15-minute cycles, focusing on energy efficiency and managing CSV files on the SD card.

### Sensor's hardware:
This document addresses hardware challenges related to sensor data storage and timestamping. It highlights issues with SD card reliability, where data loss can disrupt both recording and transmission, and proposes alternative solutions, including exploring Flash memory and investigating SD card failures. Additionally, it explains the use of internal and external RTCs for timestamping data and outlines the team's progress toward eliminating the external RTC by synchronizing time with a server in the future.

### LoRa protocol: 

This documentation provides a comprehensive guide to the design, implementation, and development of a custom local communication network protocol built on the LoRa physical layer for river monitoring. It outlines the system’s structure, challenges faced, solutions implemented, and future tasks to enhance functionality. Designed to equip future contributors with the knowledge to expand and refine the project, this guide ensures a smooth handover and successful progression.

### Gateway and server configurations

Here, we explain all the necessary steps to properly configure our Gateway. Additionally, we explain how to create the server, its applications, and register the Gateway along with the Relay on the server.

### Using Server - LoRaWAN code

Here it is explained how we can test our server and gateway setup using a test code.

Additionally, it is explained to what extent the final part of the communication, using LoRaWAN, has been developed, and what possible ideas exist to continue with the project.


## Presentation Demo

### Sensor_demo

This code includes all the functionalities of the original code, but with shorter data sampling intervals. It is designed for real-time testing, allowing for immediate measurements without waiting for the 15-minute intervals used in the original setup.

### Relay_LoraWan

This code serves as a demonstration version of the previous LoRa relay module in the Molonari system. It highlights basic functionalities such as requesting data from sensors, printing via the serial port, and testing data transmission to the LoRaWAN network server. This version is intended for testing and presentation purposes and does not include full features or optimizations.

## Relay

This file serves as the firmware for the LoRa relay module in the Molonari system, designed to handle the transmission and display of measurement data. Its current functionalities include requesting measurements from sensors and printing them to the serial port, with plans to support data transmission to a server in the future. The firmware is primarily intended for the Arduino MKR WAN 1310 hardware platform and plays a key role in enabling wireless communication within the Molonari system.

## Sensor

This firmware, designed for the **Molonari System** riverbed sensor node, integrates **data measurement**, **transmission**, and **storage** functionalities. It reads temperature and pressure data from sensors, transmits them to a server via **LoRa**, and saves the measurements in CSV format on an SD card. Key features include precise scheduling using a real-time clock (RTC), efficient low-power mode management, and debugging capabilities for **LoRa** and SD card operations. The system supports 4 calibrated temperature sensors and ensures reliable daily data collection and transmission, making it suitable for long-term environmental monitoring.

## Tests Codes

### Adjust RTC


The `Adjust_RTC` file contains a small code that handles the calibration of the real-time clock (RTC). It synchronizes time between internal and external RTC modules, adjusts the clock with a specified offset in seconds, and periodically displays the current time in a readable format via the serial port. This file ensures precise time management requiring reliable synchronization.

###  Receiver/Sender

From 2023 

This setup demonstrates basic wireless communication between two LoRa-enabled devices.

### Relay_Lora/Sensor_Lora

The **Relay_Lora** and **Sensor_Lora** codes are designed for LoRa communication in the Molonari system. **Relay_Lora** functions as a receiver, waiting for and storing incoming packets in a queue, then printing the data via serial after a handshake with the LoRa module. **Sensor_Lora** acts as the sender, creating a queue of messages and transmitting them to a relay address after establishing a connection. Both codes use LoRa for wireless communication, handle session management, and incorporate debugging and data logging features. The LED indicates the system's active status during operations.

### testArduinoLoRaWAN

This test code verifies the functionality of the **MKRWAN** library by simulating data transmission to a LoRaWAN server using OTAA authentication. It includes features like payload retries, low-power modem mode, and adaptive data rate configuration.

### testArduinoLowPower

This test code evaluates the compatibility of the **ArduinoLowPower** library with the device by implementing a counter and deep sleep functionality. It helped in understanding the library's features, such as entering and exiting deep sleep while preserving functionality like serial communication.