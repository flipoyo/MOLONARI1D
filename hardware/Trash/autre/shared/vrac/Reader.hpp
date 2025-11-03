//NOT COMPLETE AT ALL, SENSOR INTERNALS IS

// This file defines the Reader class, which is used to read a serie of measurements from a CSV file.
// See internals/Reader.cpp for the implementation.


// Check that the file has not been imported before
#ifndef READER_CLASS_H
#define READER_CLASS_H

#include <SD.h>
#include "Measure.hpp"

// The name of the csv file
extern const char filename[];

// An object to read a serie of measurements from a CSV file.
class Reader
{
    private:
        File file;
        static unsigned int line_cursor;

    public:
        // Establish a connection with the SD card.
        bool EstablishConnection(unsigned  int shift);
        
        // move the cursor to a g.
        // The cursor can only be moved forward.
        void UpdateCursor(unsigned int lineId);

        void writetomyrecourdfile();

        std::queue<String> loadDataIntoQueue();

        // Returns the Measure located at the cursor's line.
        // This function does increment the cursor.
        // Make sure that there is data availble before calling this function.
        String ReadMeasure();

        // Check if there are still lines to read.
        // Should be called before ReadMeasure() to avoid getting stuck in a loop.
        bool IsDataAvailable();

        // Call this function when you don't need the Reader anymore.
        void Dispose();
};

#include "Reader.cpp"

#endif