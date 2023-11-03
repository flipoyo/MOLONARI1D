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


PressureSensor pressureSensor(A6, 6);


void setup() {
  Serial.begin(9600);

  InitialiseLora();
  InitialiseRTC();
  bool didIt = InitialiseLog();

  if (didIt) {
    Serial.println("SD card initialized");

    // TESTINGS

    unsigned int test1[4] = {sizeof("Id,Date,Time,Capteur1,Capteur2,Capteur3,Capteur4"),sizeof("\n"),sizeof(Measure),777};
    LogData(test1);

    unsigned int test2[4] = {1,9,0,456456};
    LogData(test2);
  }
  else {
    Serial.println("SD card failed to initialize");
  }

}

void loop() {
  // Get immidiately the data stored in FlashMemory

  // PRESSURE_T pressure = pressureSensor.MeasurePressure();
  // Serial.println(pressure);

}