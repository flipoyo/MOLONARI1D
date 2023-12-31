// This file defines the Writer class, which is used to write a serie of measurements to a CSV file.
// See internals/Writer.cpp for the implementations.


// Check that the file has not been imported before
#ifndef WRITER_CLASS_H
#define WRITER_CLASS_H

#include <SD.h>
#include "Measure.hpp"

// The name of the csv file
extern const char filename[];

// An object to write a serie of measurements to a CSV file.
class Writer
{
    private:
        File file; 
        unsigned int next_id;
        int CSPin;

        // Append a Measure to the csv file.
        void WriteInNewLine(Measure data);

        // Convert the raw data into a Measure.
        void ApplyContent(Measure* measure, MEASURE_T mesure1, MEASURE_T mesure2, MEASURE_T mesure3, MEASURE_T mesure4);

        // Reconnect to the SD card.
        bool Reconnect();

    public:
        // Establish the connection with the SD card.
        void EstablishConnection(const int CSpin);

        // Process and append raw data to the csv file.
        void LogData(MEASURE_T mesure1, MEASURE_T mesure2 = 0, MEASURE_T mesure3 = 0, MEASURE_T mesure4 = 0);

        // Close the connection with the SD card.
        void Dispose();
};

#include "Writer.cpp"

#endif