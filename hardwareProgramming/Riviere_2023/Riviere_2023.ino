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

#include "internals/Lora.hpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.hpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log_Initializer.cpp"
#include "internals/Writer.hpp"

const int CSpin = 6;

int sensePin1 = A1; //This is the Arduino Pin that will read the sensor output
int sensePin2 = A2;
int sensePin3 = A3;
int sensePin4 = A4;
const int CSPin = 6;
Writer writer;



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
  bool connectionEstablished = InitialiseLog(CSpin);

  if (connected) {
    writer.EstablishConnection();
  }

}

void loop() {
    int sensorInput1 = analogRead(sensePin1); //read the analog sensor and store it
    int sensorInput2 = analogRead(sensePin2); //read the analog sensor and store it
    int sensorInput3 = analogRead(sensePin3); //read the analog sensor and store it
    int sensorInput4 = analogRead(sensePin4); //read the analog sensor and store it
    double temp1 = ConvertTemp(sensorInput1);
    double temp2 = ConvertTemp(sensorInput2);
    double temp3 = ConvertTemp(sensorInput3);
    double temp4 = ConvertTemp(sensorInput4);
    
    Serial.println(String(temp1) + "   " + String(temp2) + "   " + String(temp3) + "   " + String(temp4) + "   ");
    double test1[4] = {temp1, temp2, temp3, temp4};
    writer.LogData(test1);
    delay(15000);

  Serial.println("Logging data n°" + String(i));
  i++;

  noInterrupts();
  writer.LogData(i, 1, 2, 3);
  interrupts();

  delay(1000);
  i++;
  Serial.println(i);
  writer.LogData(41);

  delay(5000);
}