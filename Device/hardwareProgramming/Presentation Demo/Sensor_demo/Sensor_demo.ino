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
// Define the data-type of a measurement
#define MEASURE_P unsigned short
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
const char filename[] = "RECORDS.CSV"; // WARNING Format 8.3, no more than 8 characters on SD FAT32 Files

// --- Sensors Set up---

int npressure = 1; //number of pressure sensors
int ntemp = 5; //number of temperature sensors

// NF 29/4/2025 Adding temperature Shaft in MOLONARI 2025
PressureSensor **pSens;
TemperatureSensor **tempSensors;

double *pressure;
double *temperature;

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


  // Initialise SD Card
  Serial.print("Initialising SD card ...");
  bool success = InitialiseLog(CSPin,npressure,ntemp);
  if (success) {
    Serial.println(" Done");
  } else {
    Serial.println(" Failed");
    noInterrupts();
    while (true) {}
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

  int nanalogical = 1; //initialise number of analogical sensors to 1;
  int pin = nanalogical ;
  // Initialise the pressure sensors
  Serial.println("Initialising pressure sensors...");
  pSens = new PressureSensor*[npressure];
  for (int i = 0; i < npressure; i++) {
    pin = nanalogical++; // Use the analog pin number directly
    pSens[i] = new PressureSensor(pin, 1); // Initialize the object
    Serial.print("Pressure sensor ");
    Serial.print(nanalogical);
    Serial.print("on pin");
    Serial.print(pin);
    Serial.println(" initialised.");
  }

  // Initialise the temperature sensors
  Serial.println("Initialising temperature sensors...");
  tempSensors = new TemperatureSensor*[ntemp];
  for (int i = 0; i < ntemp; i++) {
    pin = nanalogical++; // Use the analog pin number directly
    tempSensors[i] = new TemperatureSensor(pin, 1, 0.5277, 101.15); // A2, A3, A4, etc.
    Serial.print("Temperature sensor ");
    Serial.print(i +1);
    Serial.print("on pin");
    Serial.print(pin);
    Serial.println(" initialised.");
  }

  // Allocate memory for pressure and temperature arrays
  pressure = new double[npressure];
  temperature = new double[ntemp];

  // Initialize the arrays to 0
  for (int i = 0; i < npressure; i++) {
    pressure[i] = 0;
  }
  for (int i = 0; i < ntemp; i++) {
    temperature[i] = 0;
  }


  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);

  Serial.println("Initialisation complete !");
}

// ----- Main Loop -----

void loop() {
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

  // Initialise SD Card
  //InitialiseLog(CSPin,npressure,ntemp);//Already Done in setup

  // Initialise the SD logger
  logger.EstablishConnection(CSPin);
  // Initialise RTC

  InitialiseRTC();
  // Initialise the measurement times
  //InitializeMeasurementTimes();
  //InitializeMeasurementCount();
  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);
  Waiter waiter;
  waiter.startTimer();

  Serial.println("");
  // Calculate the time to sleep until the next measurement
  unsigned long sleepTime = CalculateSleepTimeUntilNextMeasurement();

  // Count and check that the number of daily measurements has been reached
  measurementCount = logger.next_id;
  if (measurementCount <= TOTAL_MEASUREMENTS_PER_DAY) {
    Serial.println("——Measurement " + String(measurementCount) + "——");

    // Perform measurements
    for(int i = 0; i < npressure; i++) {
      pressure[i] = pSens[i]->MeasurePressure();
    }
    for(int i = 0; i < ntemp; i++) {
      temperature[i]= tempSensors[i]->MeasureTemperature();
    }

    logger.LogData(npressure,pressure,ntemp,temperature);
    measurementCount= logger.next_id;
  }

  // If all measurements for the day are complete, transmit data and reset the counter
  if (measurementCount >= TOTAL_MEASUREMENTS_PER_DAY) {
    Serial.println("Transmitting data via LoRa...");
    waiter.delayUntil(300000);
    Serial.println("Data transmitted. Resetting measurement count.");
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
