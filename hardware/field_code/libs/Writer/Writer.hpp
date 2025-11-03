// This file defines the Writer class, which is used to write a series of measurements to a CSV file.
// See internals/Writer.cpp for the implementations.

// Ensure that this file is only included once in compilation
#ifndef WRITER_CLASS_H
#define WRITER_CLASS_H

#include <SD.h>
#include "Measure.hpp"

// The name of the CSV file to which data will be written
extern const char filename[];

// Writer class: used to manage writing a series of measurements to a CSV file
class Writer
{
    private:
        File file; // File object for handling CSV file operations
        unsigned int next_id; // ID to keep track of the next measurement
        int CSPin; // Pin number for Chip Select (CS) to control the SD card

        // Append a measurement (of type Measure) to a new line in the CSV file
        void WriteInNewLine(Measure& data);

        // Populate a Measure object using the raw data provided
        void ApplyContent(Measure* measure, int ncapteur, double *toute_mesure);

        // Attempt to reconnect to the SD card if the connection is lost
        bool Reconnect();

    public:
        // Initialize connection with the SD card using the specified Chip Select (CS) pin
        void EstablishConnection(const int CSpin);

        // Process raw data and append it as a new entry in the CSV file
        // NF 29/4/2025 modification to pass 
        void LogData(int ncapteur, const std::vector<double>& toute_mesure);

        // Safely close the connection with the SD card
        void Dispose();
};

#endif
