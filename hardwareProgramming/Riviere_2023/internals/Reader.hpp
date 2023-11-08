
// Check that the file has not been imported before
#ifndef READER_CLASS_H
#define READER_CLASS_H

#include <SD.h>
#include "Measure.hpp"


class Reader
{
    private:
        File file;
        unsigned int line_cursor;

        Measure StringToMeasure(String line);

    public:
        Reader();

        // Establish a connection with the SD card.
        void EstablishConnection();

        // Sets the cursor to a given line.
        // The cursor can only be moved forward.
        void MoveCursor(unsigned int lineId);

        // Returns the Measure located at the cursor's line.
        // This function does increment the cursor.
        Measure ReadMeasure();

        // Check if there are still lines to read.
        // Should be called before ReadMeasure().
        bool IsDataAvailable();

        ~Reader();
};

#include "Reader.cpp"

#endif