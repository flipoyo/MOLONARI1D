// TRES DIFFERENT DE SENSOR_DEMO/INTERNALS

// This file defines the Measure class, which stores readings from all 4 sensors at a specific time.  

// Check that the file has not been imported before
#ifndef MEASURE_CLASS
#define MEASURE_CLASS

class Measure {
  public:
    // Unique ID for each measurement
    unsigned int id;
    // Date with the format "dd/mm/yyyy"
    char date[11];
    // Hour with the format "hh:mm:ss"
    char time[9];

// A PARTIR DE LA TOUT EST DIFFERENT MAIS J'AI L'IMPRESSION QUE CA FAIT LA MEME CHOSE EN MOINS 'SECURISE'

    // Value read on each sensor
    MEASURE_T chanel1;
    MEASURE_T chanel2;
    MEASURE_T chanel3;
    MEASURE_T chanel4;

    String ToString() {
      String str = "Measure n°" + String(id);
      str += " (" + String(date) + " " + String(time) + ") : ";
      str += String(chanel1) + ", " ;
      str += String(chanel2) + ", " ;
      str += String(chanel3) + ", " ;
      str += String(chanel4);
      
      return str;
    }
};

#endif