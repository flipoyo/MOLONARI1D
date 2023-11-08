/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements in an internal memory

Required hardware :
Arduino MKR WAN 1310
*/

#define MEASURE_T unsigned int
#define toRealNumber toInt

#include "internals/Lora.cpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log_Initializer.cpp"
#include "internals/Measure.h"
#include "internals/Reader.h"
#include "internals/Writer.h"

const int CSpin = 6;

Reader reader;
Writer writer;
PressureSensor pressureSensor(A6, 6);

int i = 0;

void setup() {
  Serial.begin(9600);

  while (!Serial){
  }
  
  InitialiseLora();
  InitialiseRTC();
  bool connectionEstablished = InitialiseLog(CSpin);

  if (connectionEstablished) {
    Serial.println("SD card initialized");
    // reader.EstablishConnection();
    writer.EstablishConnection();
    // TESTINGS

    
    Serial.println("Start Writing...");
    
    }


    else {
      Serial.println("SD card failed to initialize");
    }

}

void loop() {
  // PRESSURE_T pressure = pressureSensor.MeasurePressure();
  // Serial.println(pressure);
  i++;
  Serial.println(i);
  writer.LogData(41);

  delay(5000);
}