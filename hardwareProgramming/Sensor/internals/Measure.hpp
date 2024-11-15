// This file defines the Measure class, which stores readings from all 4 sensors at a specific time.  

#ifndef MEASURE_CLASS
#define MEASURE_CLASS

// Data type for the sensor measurements
#define MEASURE_T double

class Measure {
  public:
    // Unique ID for each measurement
    unsigned int id;

    // Date in the format "dd/mm/yyyy"
    char date[11];

    // Time in the format "hh:mm:ss"
    char time[9];

    // Values read from each of the 4 sensors
    MEASURE_T chanel1; // Sensor 1 reading
    MEASURE_T chanel2; // Sensor 2 reading
    MEASURE_T chanel3; // Sensor 3 reading
    MEASURE_T chanel4; // Sensor 4 reading

    /**
     * Convert the measurement details into a string representation.
     * @return A string summarizing the measurement details.
     */
    String ToString() {
      String str = "Measure n°" + String(id);                        // Add ID
      str += " (" + String(date) + " " + String(time) + ") : ";      // Add timestamp
      str += String(chanel1) + ", " ;                                // Add sensor 1 data
      str += String(chanel2) + ", " ;                                // Add sensor 2 data
      str += String(chanel3) + ", " ;                                // Add sensor 3 data
      str += String(chanel4);                                        // Add sensor 4 data
      
      return str; // Return the constructed string
    }
};

#endif
