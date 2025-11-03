// This file will contain all the code to initialise the SD card and the CSV file.


// Check that the file has not been imported before
#ifndef INTERNAL_LOG
#define INTERNAL_LOG

#include <SD.h>
#include <SPI.h>
#include <Arduino.h>
#include "Measure.hpp"


// The name of the csv file
extern const char filename[];


// Checks if the SD card has already been initialized and the file is there.
// Returns true if the file already has content; false if it doesn’t.
bool AlreadyInitialised() {
    if (!SD.exists(filename)) {
      return false;
    }
    else {
      File file = SD.open(filename);
      int a = file.available();
      file.close();
      return (a > 0); // Return true if there's data in the file
    }
}

// Generate a CSV file with a header IF it doesn’t exist yet.
// Returns true if the initialisation was successful.
bool InitialiseLog(const int CSpin,int npressure,int ntemp) {
    int i;

    String str = "Connecting To SD Card on CSpin " + String(CSpin) + " where the file " + String(filename) + " may be stored ";
    Serial.println(str);

    
    if (!SD.begin(CSpin)) {
      Serial.println("SD card initialization failed in  SD.begin(CSpin)");
      return false; // SD initialization failed
    }

    else if (!AlreadyInitialised()) {
     // char* header;
      // Par defaut si le fichier existe déjà, on l'efface
      str = "Entering Initialisation of the SD card and the file " + String(filename);
      Serial.println(str);
      if (SD.exists(filename)) {
        str = String(filename) + " exists, deleting it";
        Serial.println(str);
        SD.remove(filename); // Supprime le fichier existant
      }
      File file = SD.open(filename, FILE_WRITE); // Crée un nouveau fichier. Attention, open ouvre en mode APPEND!
      bool success = file; // Check if file opened successfully
      if (success) {
          String header = "Id,Date,Time,"    ;                    // Add ID
          for (i = 0; i < npressure ; i++) {
            header += "pressure" + String(i+1) + ", ";                             // Add sensor i data
          }                        // Add ID
          for (i = 0; i < ntemp-1 ; i++) {
            header += "temperature" + String(i+1) + ", ";                             // Add sensor i data
          }  
          header += "temperature" + String(i+1);                                        // Add last sensor data
          file.println(header); // Write header to the file
          file.close();
        }
        else {
          str = "Failed to create file " + String(filename);
          Serial.println(str);
          return false; // File creation failed
        }
      

        return success; // File already initialized!!
    }

    return true;
}


#endif