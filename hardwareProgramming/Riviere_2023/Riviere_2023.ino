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
#define LORA_DEBUG

// Uncomment this line to enable diagnostics log on serial for SD operations
#define SD_DEBUG


// ----- Imports -----

#include "internals/Lora.hpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.hpp"
#include "internals/Time.cpp"
#include "internals/SD_Initializer.cpp"
#include "internals/Writer.hpp"
#include "internals/Waiter.hpp"
#include <ArduinoLowPower.h>
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
TemperatureSensor tempSensor1(A1, 1, 0.5, 100);
TemperatureSensor tempSensor2(A2, 2, 0.5, 100);
TemperatureSensor tempSensor3(A3, 3, 0.5, 100);
TemperatureSensor tempSensor4(A4, 4, 0.5, 100);

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
  Serial.print("Initialising LoRa ...");
  InitialiseLora();
  Serial.println(" Done");

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

  // Initialise the measurement times
  Serial.print("Initialising measurement control");
  InitializeMeasurementTimes();
  InitializeMeasurementCount();
  Serial.println(" Done");

  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);

  Serial.println("Initialisation complete !");
}

// ----- Main Loop -----

int initialstartup = 0;
void loop() {
  // Initialise Serial
  Serial.begin(115200);
  // Wait up to 5 seconds for serial to connect
  unsigned long end_date = millis() + 5000; 
  while (!Serial && millis() < end_date) {
    // Do nothing
  }
  // Initialise LoRa
  InitialiseLora();
  // Initialise SD Card
  InitialiseLog(CSPin);
  // Initialise the SD logger
  logger.EstablishConnection(CSPin);
  // Initialise RTC
  InitialiseRTC();
  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);

  Waiter waiter;
  waiter.startTimer();
  // Initial start-up don't take measure
  if (initialstartup < 1) {
    initialstartup++;
    // Calculate the time to sleep until the next measurement
    unsigned long firstsleep = CalculateSleepTimeUntilNextMeasurement();
    // Enter low power mode
    Serial.end();
    waiter.sleepUntil(firstsleep);
  }
  else {
    Serial.println("");
    // Count and check that the number of daily measurements has been reached
    if (measurementCount < TOTAL_MEASUREMENTS_PER_DAY) {
      Serial.println("——Measurement " + String(NbMeasurements) + "——");
      // Perform measurements
      TEMP_T temp1 = tempSensor1.MeasureTemperature();
      TEMP_T temp2 = tempSensor2.MeasureTemperature();
      TEMP_T temp3 = tempSensor3.MeasureTemperature();
      TEMP_T temp4 = tempSensor4.MeasureTemperature();

      logger.LogData(temp1, temp2, temp3, temp4);
    
      // Increase count
      measurementCount++;
      NbMeasurements++;
    }

    // Calculate the time to sleep until the next measurement
    unsigned long sleepTime = CalculateSleepTimeUntilNextMeasurement();

    // If all measurements for the day are complete, transmit data and reset the counter
    if (measurementCount >= TOTAL_MEASUREMENTS_PER_DAY) {
      Serial.println("Transmitting data via LoRa...");
      waiter.delayUntil(60000);
      Serial.println("Data transmitted. Resetting measurement count.");
      // Reset the count and number for the next day's measurements
      measurementCount = 0;
      NbMeasurements = 1;
    }

    // Test code
    /*
    Serial.print("year: ");
    Serial.println(internalRtc.getYear());
    Serial.print("Month: "); 
    Serial.println(internalRtc.getMonth());
    Serial.print("Day: ");
    Serial.println(internalRtc.getDay());
    Serial.print("Hour: "); 
    Serial.println(internalRtc.getHours());
    Serial.print("Minute: "); 
    Serial.println(internalRtc.getMinutes());
    Serial.print("Second: "); 
    Serial.println(internalRtc.getSeconds());
    */

    // Enter low power mode
    Serial.end();
    waiter.sleepUntil(sleepTime);
  }
}