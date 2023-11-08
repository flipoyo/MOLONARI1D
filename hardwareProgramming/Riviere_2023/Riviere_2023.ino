/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements in an internal memory

Required hardware :
Arduino MKR WAN 1310
*/

#define MEASURE_T unsigned short
#define TO_MEASURE_T toInt

//#define LORA_DEBUG

#include "internals/Lora.hpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log_Initializer.cpp"
#include "internals/Writer.hpp"

const int CSpin = 6;

Writer writer;
PressureSensor pressureSensor(A6, 6);

int i = 0;

void setup() {
  // Initialise Serial
  Serial.begin(9600);
  while(!Serial) {}

  // Initialise LoRa
  Serial.println("Initialising LoRa");
  InitialiseLora();
  Serial.println("Done");

  // Initialise SD Card
  Serial.println("Initialising SD card");
  bool success = InitialiseLog(CSpin);
  if (success) {
    Serial.println("Done successfully");
  } else {
    Serial.println("Failed to initialise SD");
    noInterrupts();
    while(true) {}
  }

  writer.EstablishConnection();

  // Initialise RTC
  InitialiseRTC();
}

void loop() {
  // PRESSURE_T pressure = pressureSensor.MeasurePressure();
  // Serial.println(pressure);

  Serial.println("Logging data n°" + String(i));
  i++;

  noInterrupts();
  writer.LogData(i, 1, 2, 3);
  interrupts();

  delay(5000);
}