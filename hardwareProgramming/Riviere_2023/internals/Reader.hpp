// This file defines the Reader class, which is used to read a serie of measurements from a CSV file.
// See internals/Reader.cpp for the implementation.


// Check that the file has not been imported before
#ifndef READER_CLASS_H
#define READER_CLASS_H

#include <SD.h>
#include "Measure.hpp"


// An object to read a serie of measurements from a CSV file.
class Reader
{
    private:
        File file;
        unsigned int line_cursor;

        Measure StringToMeasure(String line);

    public:
        // Establish a connection with the SD card.
        void EstablishConnection();

        // Sets the cursor to a given line.
        // The cursor can only be moved forward.
        void MoveCursor(unsigned int lineId);

        // Returns the Measure located at the cursor's line.
        // This function does increment the cursor.
        // Make sure that there is data availble before calling this function.
        Measure ReadMeasure();

        // Check if there are still lines to read.
        // Should be called before ReadMeasure() to avoid getting stuck in a loop.
        bool IsDataAvailable();

        // Call this function when you don't need the Reader anymore.
        void Dispose();
};

#include "Reader.cpp"

#endif