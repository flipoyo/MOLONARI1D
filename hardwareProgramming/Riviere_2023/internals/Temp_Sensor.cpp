
// Check that the file has not been imported before
#ifndef TEMP_SENSOR
#define TEMP_SENSOR

// This file will contain all the code relative to the measurement of temperature
// The data type of a temperature measurement
#define TEMP_T unsigned short


// Initialise the temperature sensor for the first time. 
void InitialiseTempSensor(int alimPin, int measurePin) {
  // Attribute a pin to the temperature measurement and the power
  pinMode(alimPin, OUTPUT);
  pinMode(measurePin, INPUT);
  
}

// Measure the temperature
TEMP_T MeasureTemperature(int alimPin, int measurePin) {
  //Power the sensor only when we measure
  //Read the measured temperature on the defined pin
  //Unpower the sensor
  digitalWrite(alimPin, HIGH);
  unsigned int temp = analogRead(measurePin);
  digitalWrite(alimPin, LOW);
  return temp;
}

#endif