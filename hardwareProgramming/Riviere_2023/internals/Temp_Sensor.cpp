// This file contains all the code relative to the measurement of pressure
// See internals/Temp_Sensor.hpp for the definitions.

// Check that the file has not been imported before
#ifndef TEMP_SENSOR
#define TEMP_SENSOR

#include "Temp_Sensor.hpp"


// Initialise the temperature sensor for the first time. 
TemperatureSensor::TemperatureSensor(int _dataPin, int _enablePin, float _offset, float _scale) : dataPin(_dataPin), enablePin(_enablePin), offset(_offset), scale(_scale) {
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
  delay(200);
  TEMP_T temp = analogRead(dataPin);
  digitalWrite(enablePin, LOW);
  return (temp*3.3/4096-offset)*scale;
}

#endif