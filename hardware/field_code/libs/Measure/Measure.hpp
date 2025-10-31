// This file defines the Measure and Sensor class 

// fusionner mesure pression et température 
// fusionner temp_sensor, pressure_sensor et measure en un seul fichier measure
// measure prend en argument le pin du port, et si c'est pression ou température, et comment tu transformes les tensions en mesure
// les arguments à prendre sont : int _dataPin, int _enablePin, float _offset, float _scale comme dans temp sensor

// renvoyer la valeur de la pression et celle de la température (dans temp sensor on fait ces calculs)
// regarder ce que fait analog read 

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
        Sensor(int dataPin, int enablePin, String type_capteur, String id_box);
        int exists = 1;//temporary, just for debug, should be discarded when code is functional
        // Measure the pressure
        double get_voltage();

    private :
        // Pin to read data from (Analog pin)
        const int dataPin;
        // Pin to enable/disable the sensor
        const int enablePin = 1;  
        const String type_capteur;
        const String id_box;
};

class Measure {
  public:
    Measure(int ncapt, const std::vector<double>& toute_mesure);
    // Unique ID for each measurement
    unsigned int id;

    String date;
    String time;
    unsigned long time_in_second;

    int ncapt;

    std::vector<double> channel;

 
    String oneLine();
    String ToString();
};

#endif
