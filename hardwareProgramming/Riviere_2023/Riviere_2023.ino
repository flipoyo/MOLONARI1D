/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements in an internal memory

Required hardware :
Arduino MKR WAN 1310
*/

#include "internals/Lora.cpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log.cpp"
#include "internals/Measure.h"
#include "internals/testSample.h"
#include "internals/InternalData.h"


PressureSensor pressureSensor(A6, 6);


void setup() {
  InitialiseLora();
  InitialiseRTC();

  Serial.begin(9600);
  InitialiseLog();

  // TESTINGS
  delay(5000);

  testSample test1;
  strncpy(test1.date,"27/10/2023",21);
  test1.mesure1 = 1111;
  test1.mesure2 = 2222;
  test1.mesure3 = 3333;
  test1.mesure4 = 4444;

  LogData(test1);

  delay(5000);

  testSample test2;
  strncpy(test2.date,"27/10/2023",21);
  test2.mesure1 = 72;
  test2.mesure2 = 73;
  test2.mesure3 = 0;
  test2.mesure4 = 0;

  LogData(test2);

  delay(5000);

  testSample test3;
  strncpy(test3.date,"27/10/2023",21);
  test3.mesure1 = 1;
  test3.mesure2 = 2;
  test3.mesure3 = 3;
  test3.mesure4 = 4;

  LogData(test3);

  delay(5000);

  DisplayFlashMemory();
}

void loop() {
  // Get immidiately the data stored in FlashMemory

  // PRESSURE_T pressure = pressureSensor.MeasurePressure();
  // Serial.println(pressure);

}