#include "internals/Internal_Log.cpp"
int sensePin1 = A1; //This is the Arduino Pin that will read the sensor output
int sensePin2 = A2;
int sensePin3 = A3;
int sensePin4 = A4;


double ConvertTemp(int measure){
  return ((double)measure*5/1024-0.5)*100;
}

void setup() {
  Serial.begin(9600);
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
}