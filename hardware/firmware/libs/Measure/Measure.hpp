#ifndef MEASURE_CLASS
#define MEASURE_CLASS

#include <vector>
#include <string>
#include <Arduino.h>


class Sensor {
    public :
        Sensor(); // Default constructor
        // Initialise the sensor for the first time. 
        // dataPin -> Analog input to read data from (Analog pin)
        // enablePin -> Digital output to enable/disable the sensor 
        Sensor(int dataPin, int enablePin, String type_capteur);
        int exists = 1;//temporary, just for debug, should be discarded when code is functional
        
        double get_voltage();

    private :
        // Pin to read data from (Analog pin)
        const int dataPin;
        // Pin to enable/disable the sensor
        const int enablePin = 4;  
        const String type_capteur;

};

class Measure {
  public:
    Measure(int ncapt, const std::vector<double>& toute_mesure, String uidString);
    // Unique ID for each measurement
    unsigned int id;

    String date;
    String time;
    unsigned long time_in_second;

    int ncapt;

    std::vector<double> channel;
    String uidString;
 
    String oneLine();
    String ToString();
};

#endif
