#include "internals/Internal_Log_Initializer.cpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Writer.h"

int sensePin1 = A1; //This is the Arduino Pin that will read the sensor output
int sensePin2 = A2;
int sensePin3 = A3;
int sensePin4 = A4;
const int CSPin = 6;
Writer writer;

double ConvertTemp(int input){
  return ((double)input*3.3/1024-0.5)*100;
}

void setup() {

  
  bool connected = InitialiseLog(CSPin);

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
}