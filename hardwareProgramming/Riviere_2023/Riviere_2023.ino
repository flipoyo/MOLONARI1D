/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements in an internal memory

Required hardware :
Arduino MKR WAN 1310
*/

#include "internals/Lora.hpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log.cpp"
#include "internals/Measure.h"
// #include "internals/testSample.h" Deprecated
// #include "internals/InternalData.h" Deprecated



void setup() {
  Serial.begin(9600);

  while(!Serial) {}


  Serial.println("Initialising LoRa");
  InitialiseLora();
  Serial.println("Done");

  Serial.println("Initialising SD card");
  bool success = InitialiseLog();
  if (success) {
    Serial.println("Done successfully");
  } else {
    Serial.println("Failed to initialise SD");
    noInterrupts();
    while(true) {}
  }

  InitialiseRTC();
}

unsigned int i = 0;

void loop() {
  // Get immidiately the data stored in FlashMemory

  // PRESSURE_T pressure = pressureSensor.MeasurePressure();
  // Serial.println(pressure);

  Serial.println("Logging data n°" + String(i));
  i++;
  unsigned int raw_measure[4] = {i, 1, 2, 3};

  noInterrupts();
  LogData(raw_measure);
  interrupts();

  delay(1000);
}