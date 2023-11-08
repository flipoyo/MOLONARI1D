// This file will contain all the code relative to the measurement of pressure


// Check that the file has not been imported before
#ifndef TEMP_SENSOR_H
#define TEMP_SENSOR_H

// The data type of a temperature measurement
#define TEMP_T double


class TemperatureSensor {
    public :
        // Initialise the temperature sensor for the first time. 
        // dataPin -> Analog input to read data from (Analog pin)
        // enablePin -> Digital output to enable/disable the sensor 
        TemperatureSensor(int dataPin, int enablePin);
        
        // Measure the temperature
        TEMP_T MeasureTemperature();

    private :
        // Pin to read data from (Analog pin)
        const int dataPin;
        // Pin to enable/disable the sensor
        const int enablePin;
};

#include "Temp_Sensor.cpp"

#endif