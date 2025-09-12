// This file contains all the code relative to the measurement of pressure
// See internals/Pressure_Sensor.hpp for the definitions.


// Check that the file has not been imported before
#ifndef PRESSURE_SENSOR
#define PRESSURE_SENSOR


#include "Pressure_Sensor.hpp"


PressureSensor::PressureSensor(const int _dataPin, const int _enablePin) : dataPin(_dataPin), enablePin(_enablePin) {
  pinMode(enablePin, OUTPUT);

  analogReadResolution(12);   // Set precision to 12 bit (maximum of this board)
}

PRESSURE_T PressureSensor::MeasurePressure() {
  digitalWrite(enablePin, HIGH);    // Enable the sensor
  delay(50);    // Wait for it to enable

  PRESSURE_T pressure = analogRead(dataPin);  // Read data

  digitalWrite(enablePin, LOW);   // Disable the sensor back

  return pressure;
}


#endif