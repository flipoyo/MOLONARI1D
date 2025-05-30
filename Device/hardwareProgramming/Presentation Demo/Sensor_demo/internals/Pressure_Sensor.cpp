// This file contains all the code relative to the measurement of pressure
// See internals/Pressure_Sensor.hpp for the definitions.


// Check that the file has not been imported before
#ifndef PRESSURE_SENSOR
#define PRESSURE_SENSOR


#include "Pressure_Sensor.hpp"
PressureSensor::PressureSensor() : dataPin(-1), enablePin(-1) {
  // Default constructor body (if needed)
}

PressureSensor::PressureSensor(const int _dataPin, const int _enablePin) : dataPin(_dataPin), enablePin(_enablePin) {
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);

  analogReadResolution(12);   // Set precision to 12 bit (maximum of this board)
}

double PressureSensor::MeasurePressure() {
  digitalWrite(enablePin, HIGH);    // Enable the sensor
  delay(50);    // Wait for it to enable

  double pressure = (double) analogRead(dataPin);  // Read data

  digitalWrite(enablePin, LOW);   // Disable the sensor back

  return pressure;
}


#endif