<<<<<<< HEAD
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
#include "internals/Internal_Log_Initializer.cpp"
#include "internals/Measure.h"
#include "internals/Reader.h"
#include "internals/Writer.h"
=======
#include "internals/Internal_Log.cpp"
int sensePin1 = A1; //This is the Arduino Pin that will read the sensor output
int sensePin2 = A2;
int sensePin3 = A3;
int sensePin4 = A4;
>>>>>>> 2023bradesi

const int CSpin = 6;

<<<<<<< HEAD
// Reader reader;
Writer writer;
PressureSensor pressureSensor(A6, 6);

=======
double ConvertTemp(int measure){
  return ((double)measure*5/1024-0.5)*100;
}
>>>>>>> 2023bradesi


void setup() {
  Serial.begin(9600);
<<<<<<< HEAD

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


    for (int i=0; i<5; i++){

      unsigned int test[4] = {41,55455,123,1};
      writer.LogData(test);

      unsigned int test1[4] = {7,3,0,2};
      writer.LogData(test1);
    }

    
    Serial.println("Finished Writing");


    }


    else {
      Serial.println("SD card failed to initialize");
    }

}

void loop() {
  // PRESSURE_T pressure = pressureSensor.MeasurePressure();
  // Serial.println(pressure);
=======
  bool didIt = InitialiseLog();
  while (!Serial){
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
    Serial.println(String(temp1) + "  " + String(temp2) + "  " +String(temp3) +"  " + String(temp4) );
    

    double test1[4] = {temp1, temp2, temp3, temp4};
    LogData(test1);
    delay(1000);
>>>>>>> 2023bradesi
}