/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements on an SD card

Required hardware :
 - Arduino MKR WAN 1310
 - Featherwing Adalogger
*/


// ----- Configurations -----

// Define the data-type of a measurement
#define MEASURE_T double
// Define a function to parse a measurement (i.e. to convert a string to a MEASURE_T)
#define TO_MEASURE_T toDouble

// Uncomment this line to enable diagnostics log on serial for lora operations
//#define LORA_DEBUG

// Uncomment this line to enable diagnostics log on serial for SD operations
//#define SD_DEBUG


// ----- Imports -----

#include "internals/Lora.hpp"
#include "internals/Low_Power.hpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.hpp"
#include "internals/Time.cpp"
#include "internals/SD_Initializer.cpp"
#include "internals/Writer.hpp"
#include "internals/Waiter.hpp"
// #include "internals/FreeMemory.cpp"


// ----- Main Variables -----

// --- SD ---
// The chip select pin of the SD card
const int CSPin = 5;
// The SD logger to write measurements into a csv file
Writer logger;
// The name of the csv file where the measurements will be saved
const char filename[] = "RIVIERE.CSV";

// --- Sensors ---
TemperatureSensor tempSensor1(A1, 1);
TemperatureSensor tempSensor2(A2, 2);
TemperatureSensor tempSensor3(A3, 3);
TemperatureSensor tempSensor4(A4, 4);


// ----- Main Setup -----

void setup() {
  // Enable the builtin LED during initialisation
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialise Serial
  Serial.begin(115200);

  // Wait up to 5 seconds for serial to connect
  unsigned long end_date = millis() + 5000; 
  while (!Serial && millis() < end_date) {
    // Do nothing
  }


  // Initialise LoRa
  Serial.println("Initialising LoRa");
  InitialiseLora();
  Serial.println("Done");

  // Initialise SD Card
  Serial.print("Initialising SD card ...");
  bool success = InitialiseLog(CSPin);
  if (success) {
    Serial.println(" Done");
  } else {
    Serial.println(" Failed");
    noInterrupts();
    while(true) {}
  }

  // Initialise the SD logger
  Serial.print("Loading log file ...");
  logger.EstablishConnection(CSPin);
  Serial.println(" Done");

  // Initialise RTC
  Serial.print("Initialising RTC ...");
  InitialiseRTC();
  Serial.println(" Done");

  Serial.println("Initialisation complete !");
  Serial.println();

  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);


  // End Lora
  LoRa.end();

  // Reset Lora
  pinMode(LORA_RESET, OUTPUT);
  digitalWrite(LORA_RESET, LOW);
  delay(10);
  digitalWrite(LORA_RESET, HIGH);
  pinMode(LORA_RESET, INPUT);
  
  // Turn off the processor
  LowPower.deepSleep();
}


// ----- Main Loop -----

void loop() {
  // Turn off the processor
  LowPower.deepSleep();
}