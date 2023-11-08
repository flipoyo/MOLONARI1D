
// Check that the file has not been imported before
#ifndef TEMP_SENSOR
#define TEMP_SENSOR

#include "Temp_Sensor.hpp"


// Initialise the temperature sensor for the first time. 
TemperatureSensor::TemperatureSensor(int _dataPin, int _enablePin) : dataPin(_dataPin), enablePin(_enablePin) {
  // Attribute a pin to the temperature measurement and the power
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);
  
  analogReadResolution(12);   // Set precision to 12 bit (maximum of this board)
}

// Measure the temperature
TEMP_T TemperatureSensor::MeasureTemperature() {
  //Power the sensor only when we measure
  digitalWrite(enablePin, HIGH);

  delay(50);

  //Read the measured temperature on the defined pin
  unsigned int temp = analogRead(dataPin);

  //Unpower the sensor
  digitalWrite(enablePin, LOW);
  return temp;
}

#endif