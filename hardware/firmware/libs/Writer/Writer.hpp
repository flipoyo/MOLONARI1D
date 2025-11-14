#ifndef WRITER_CLASS_H
#define WRITER_CLASS_H

#include <SD.h>
#include "Measure.hpp"

// The name of the CSV file to which data will be written
extern const char filename[];

class Writer
{
    private:
        File file;
        unsigned int next_id; 
        int CSPin; 

        // Append a measurement (of type Measure) to a new line in the CSV file
        void WriteInNewLine(Measure& data);

        // Attempt to reconnect to the SD card if the connection is lost
        bool Reconnect();

    public:
        // Initialize connection with the SD card using the specified Chip Select (CS) pin
        void EstablishConnection(const int CSpin);

        // NF 29/4/2025 modification to pass 
        void LogData(int ncapteur, const std::vector<double>& toute_mesure, String uidString);
        void LogString(std::queue<String> receiveQueue);

        // Safely close the connection with the SD card
        void Dispose();
};

#endif
