# Understanding our sensor code

Work of MOLONARI2024 team 

## Introduction
Since this project is intended to be developed and improved each year by a new group of students, we created this document to explain the structure and functionality of the main sensor code and its associated classes. This document serves as a general guide to understanding the sensor code (.ino), detailing the organization and purpose of each file, class (.cpp and .hpp), and main function. The aim is to make future modifications or improvements easier to implement and understand.

## Main code: Riviere_2024.ino
This code is uploaded to our Arduino board and contains the setup and main loop of our system. It manages the overall workflow and calls the necessary classes. It contains the following parts: the initialization, the setup and the loop.

### Initialization
* Configurations. Here we define the data type for measurements, specifie a function for parsing measurements as TO_MEASURE_T, and include options to enable diagnostic logging for LoRa operations and SD card operations.
* Imports. Be sure you are including the necessary header files and source files for the sensor firmware.
* Main Variables. This section declares:
 - The CSPin constant, which specifies the chip select pin for the SD card and is set to pin 5 in this case. You can change this to another unused pin number, but it should not be set to pin 6 (see the installation guide). In simple terms, this pin *establishes communication* between the microcontroller and the SD card.
 - An instance of the Writer class named logger, which facilitates writing measurement data to a CSV file
 - The filename for this CSV file is defined as RIVIERE.CSV
 - Four instances of the Temp_Sensor class are initialized, each assigned to a specific analog pin (A1, A2, A3, A4) and given unique identifiers (1, 2, 3, 4).

### Setup()
In the setup function, the initialization of various system components is performed. 
First, the LED is enabled and lights up to indicate that the system is **ready to start**. Next, the serial communication is established and the system waits up to 5 seconds for the connection to be established.

The LoRa communication is then initialized. "Initialising LoRa” is printed to indicate the start of this process. 

The SD card is initialized using CSPin. If successful, a confirmation message is displayed; if not, an error message appears, interrupts are disabled, and the system enters an infinite loop to halt further operations.

With the SD card ready, the logger establishes a connection and the RTC is initialized, confirmed by a serial message.

Finally, a message is printed indicating that the initialization is complete. Before the end of the function, the LED goes off indicating that the **system is ready for operation**.

In summary, once the set up is initialized and before starting the loop, the serial monitor should look like this:

*Initialising LoRa*
*Done*
*Initialising SD card*
*Done*
*Loading log file ...*
*Done*
*Initialising RTC ...*
*Done*
*Initialisation complete !*

### Loop()

The main cycle flow is designed to take readings at specific intervals of 15 minutes. If the system has just started, it waits until the next measurement interval without taking readings to synchronize with the set time. At each measurement interval, the system checks to see if it has reached the required number of daily measurements (96 mesurements). If it has not, it takes temperature readings from the sensors and records them on the SD card. After each measurement, the system calculates the waiting time until the next measurement and re-enters the low power mode.

When all daily measurements have been completed, the system transmits the accumulated data through LoRa, waits a short period and then resets the measurement counter for the next day. This logic ensures that the system meets the required number of measurements and efficiently manages energy resources, alternating between activity and low-power standby.

To understand better the logic behind the main loop, we recommend you to take a look at the flowchart in ...

## Classes: What we need to make this code work

**Lora:**
This class handles LoRa communication. Its main functions include LoRa initialization, sending and receiving packets with integrity control through checksums, and managing the communication session (start, close, and data transmission). It is also responsible for performing a handshake process (SYN-ACK) to establish reliable communication between devices.
**Low_power:**
This class is designed to control and manage low-power mode on an Arduino-based device, helping to reduce power consumption by disabling non-essential features during periods of inactivity.
**Measure:**
This class is designed to store a measurement with the values obtained from the 4 sensors at a particular time. In addition, it has a method that allows converting the measurement data to a readable format.
**Pressure_Sensor:**
The PressureSensor class is responsible for initializing the sensor and taking pressure readings via a data pin. It also handles the activation and deactivation of the sensor via an enable pin.
**Reader:**
The Reader class is used to read a series of measurements from a CSV file and handle the cursor within the file. 
**SD_Initializer:**
This file contains functions related to initializing the SD card and verifying whether the CSV file already exists and has data.
**Temp_Sensor:**
This file manages the temperature measurement using a temperature sensor. The TemperatureSensor class defines two methods to measure the temperature, and provides the necessary functions to initialize and read the sensor.
**Time:**
This file contains all the necessary code to manage the time in your system using two RTC modules: the internal RTC of the Arduino MKR and an external RTC (PCF8523). It also manages the taking of temperature or pressure measurements in 15-minute intervals throughout the day, with the possibility to calculate and program the time to wait between measurements.
**Waiter:**
This file defines a class called Waiter that manages wait time efficiently, using low-power modes and the ability to perform LoRa communications during wait periods. In addition, it allows you to measure the time it takes to perform tasks (such as measurements or data saving) based on a timer that you can start and use throughout the main program cycle.
**Writer:**
This file defines the Writer class, which is responsible for recording measurement data in a CSV file on an SD card. 




