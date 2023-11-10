
// Check that the file has not been imported before
#ifndef TEMP_SENSOR
#define TEMP_SENSOR

#include "Temp_Sensor.hpp"


// Initialise the temperature sensor for the first time. 
TemperatureSensor::TemperatureSensor(int _dataPin, int _enablePin) : dataPin(_dataPin), enablePin(_enablePin) {
  // Attribute a pin to the temperature measurement and the power
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);
  
  analogReadResolution(12);   // Set precision to 12 bit (maximum of this board)
}

// Measure the temperature
TEMP_T TemperatureSensor::MeasureTemperature() {
  //Power the sensor only when we measure
  digitalWrite(enablePin, HIGH);
  delay(50);
  TEMP_T temp = analogRead(dataPin);
  digitalWrite(enablePin, LOW);
  return (temp*3.3/4096-0.5)*100;
}

#endif