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

// The first line of the CSV file
const char header[] = "Id,Date,Time,Capteur1,Capteur2,Capteur3,Capteur4";

// Returns wheather the SD card wad already initialised or not.
bool AlreadyInitialised() {
    if (!SD.exists(filename)) {
      return false;
    }
    else {
      File file = SD.open(filename);
      int a = file.available();
      file.close();
      return (a > 0);
    }
}

// Generate a CSV file with a header IF necessary.
// Rturns true if the initialisation was successful.
bool InitialiseLog(const int CSpin) {
    if (!SD.begin(CSpin)) {
      return false;
    }

    else if (!AlreadyInitialised()) {
        File file = SD.open(filename, FILE_WRITE);
        bool success = file;
        if (success) {
            file.println(header);
        }
        file.close();

        return success;
    }

    return true;
}


#endif