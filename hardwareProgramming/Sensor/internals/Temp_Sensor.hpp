// This file contains all the code relative to the measurement of pressure
// See internals/Temp_Sensor.cpp for the implementation.


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
        TemperatureSensor(int dataPin, int enablePin, float offset, float scale);
        
        // Measure the temperature
        TEMP_T MeasureTemperature();
        TEMP_T MeasureTemperature2();
        
    private :
        // Pin to read data from (Analog pin)
        const int dataPin;
        // Pin to enable/disable the sensor
        const int enablePin;
        // Calibration coefficients
        const float offset;  
        const float scale;   
};

#include "Temp_Sensor.cpp"

#endif