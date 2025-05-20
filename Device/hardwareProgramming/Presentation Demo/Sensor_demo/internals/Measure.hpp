// This file defines the Measure class, which stores readings from all 4 sensors at a specific time.  

#ifndef MEASURE_CLASS
#define MEASURE_CLASS


class Measure {
  public:
    // Unique ID for each measurement
    unsigned int id;

    // Date in the format "dd/mm/yyyy"
    char date[11];

    // Time in the format "hh:mm:ss"
    char time[9];

    int npressure; // number of pressure sensors
    int ntemp; // number of sensors

    double *chanelP; // pointer to the value of the pressure analogical sensors 
    double *chanelT; // pointer to the value of the temperature analogical sensors 

    // Constructor
    Measure(int npressure, int ntemp) : npressure(npressure), ntemp(ntemp) {
      // Allocate memory for pressure and temperature channels
      this->npressure = npressure; // Assign number of pressure sensors
      this->ntemp = ntemp; // Assign number of temperature sensors
      this->chanelP = new double[npressure]; // Allocate memory for pressure values
      this->chanelT = new double[ntemp]; // Allocate memory for temperature values
      // Initialize the channels with default values (e.g., 0.0)
      for (int i = 0; i < npressure; i++) {
        this->chanelP[i] = 0.0;
      }
      for (int i = 0; i < ntemp; i++) {
        this->chanelT[i] = 0.0;
      }
    }

    // Destructor
    ~Measure() {
      // Free the allocated memory
      delete[] chanelP;
      delete[] chanelT;
    }

     // Method to generate a one-line string representation of the measurement
    String oneLine() {
      int i;
      String str = String(id);                        // Add ID
      str += " (" + String(date) + " " + String(time) + ") : ";      // Add timestamp
      for (i = 0; i < npressure ; i++) {
        str += String(chanelP[i]) + ", ";                             // Add sensor i data
      }  
      for (i = 0; i < ntemp-1 ; i++) {
        str += String(chanelT[i]) + ", ";                             // Add sensor i data
      }                             // Add sensor 3 data
    str += String(chanelT[i]);                                        // Add last sensor data
    
    return str; // Return the constructed string
    }

    /**
     * Convert the measurement details into a string representation.
     * @return A string summarizing the measurement details.
     */
    String ToString() {
      int i;
      String str = "Measure n°" + oneLine();                                      // Add last sensor data
    
    return str; // Return the constructed string
    }  
};

#endif
