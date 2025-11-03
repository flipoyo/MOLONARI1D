// NOT COMPLETE AT ALL, USES STRING LIBRARY


// This file will contain all the code to initialise the SD card and the CSV file.


// Check that the file has not been imported before
#ifndef INTERNAL_LOG
#define INTERNAL_LOG

#include <SD.h>
#include <SPI.h>
#include <String.h>
#include "Measure.hpp"


// The name of the csv file
extern const char filename[];

// Header row for the CSV file
const char header[] = "Id,Date,Time,Capteur1,Capteur2,Capteur3,Capteur4";

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
bool InitialiseLog(const int CSpin) {
    if (!SD.begin(CSpin)) {
      return false; // SD initialization failed
    }

    else if (!AlreadyInitialised()) {
      // If the file isn’t initialized, open it and add the header
        File file = SD.open(filename, FILE_WRITE);
        bool success = file; // Check if file opened successfully
        if (success) {
            file.println(header); // Write header to the file
        }
        file.close();

        return success; // File already initialized!!
    }

    return true;
}


#endif