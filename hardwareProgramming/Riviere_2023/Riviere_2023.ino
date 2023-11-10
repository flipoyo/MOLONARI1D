/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements in an internal memory

Required hardware :
Arduino MKR WAN 1310
*/

#define MEASURE_T double
#define TO_MEASURE_T toDouble

#define LORA_DEBUG

#include "internals/Lora.hpp"
#include "internals/Low_Power.hpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.hpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log_Initializer.cpp"
#include "internals/Writer.hpp"

const int CSPin = 6;
Writer writer;
TemperatureSensor tempSensor1(A1, 1);
TemperatureSensor tempSensor2(A2, 2);
TemperatureSensor tempSensor3(A3, 3);
TemperatureSensor tempSensor4(A4, 4);


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
  bool success = InitialiseLog(CSPin);
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
  TEMP_T temp1 = tempSensor1.MeasureTemperature();
  TEMP_T temp2 = tempSensor2.MeasureTemperature();
  TEMP_T temp3 = tempSensor3.MeasureTemperature();
  TEMP_T temp4 = tempSensor4.MeasureTemperature();
  
  Serial.println(String(temp1) + "   " + String(temp2) + "   " + String(temp3) + "   " + String(temp4) + "   ");  
  noInterrupts();
  writer.LogData(temp1, temp2, temp3, temp4);
  interrupts();

  delay(1000);

  // Decoment to use low-power mode
  // Warning : Low-power mode is not tested yet
  //MyLowPower.Sleep(1000);
}