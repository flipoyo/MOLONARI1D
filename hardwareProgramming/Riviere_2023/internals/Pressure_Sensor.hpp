// This file contains all the code relative to the measurement of pressure
// See internals/Pressure_Sensor.cpp for the implementation.


// Check that the file has not been imported before
#ifndef PRESSURE_SENSOR_H
#define PRESSURE_SENSOR_H

// The data type of a pressure measurement
#define PRESSURE_T unsigned short


class PressureSensor {
    public :
        // Initialise the pressure sensor for the first time. 
        // dataPin -> Analog input to read data from (Analog pin)
        // enablePin -> Digital output to enable/disable the sensor 
        PressureSensor(int dataPin, int enablePin);
        
        // Measure the pressure
        PRESSURE_T MeasurePressure();

    private :
        // Pin to read data from (Analog pin)
        const int dataPin;
        // Pin to enable/disable the sensor
        const int enablePin;
};

#include "Pressure_Sensor.cpp"

#endif