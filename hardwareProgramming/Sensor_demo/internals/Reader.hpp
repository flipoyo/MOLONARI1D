// This file defines the Reader class, which is used to read a series of measurements from a CSV file.
// Refer to internals/Reader.cpp for the implementation.

#ifndef READER_CLASS_H
#define READER_CLASS_H

#include <SD.h>
#include "Measure.hpp"

// The name of the CSV file to read
extern const char filename[];

// The Reader class handles reading a series of measurements from a CSV file on an SD card.
class Reader
{
    private:
        File file; // Object for handling file operations
        static unsigned int line_cursor; // Keeps track of the current reading position in the file

    public:
        /**
         * Establish a connection with the SD card.
         * @param shift The line offset from where the reading should begin.
         * @return True if the connection is successful; false otherwise.
         */
        bool EstablishConnection(unsigned int shift);
        
        /**
         * Update the cursor position to a specific line in the file.
         * @param lineId The line number to set as the new cursor position.
         * Note: The cursor can only move forward in the file.
         */
        void UpdateCursor(unsigned int lineId);

        /**
         * Save the current cursor position and handshake status to a record file.
         * This ensures the reading process can resume later from the same position.
         */
        void writetomyrecourdfile();

        /**
         * Load data from the CSV file into a queue.
         * @return A queue containing the data read from the file.
         */
        std::queue<String> loadDataIntoQueue();

        /**
         * Read the measurement located at the current cursor position in the file.
         * This operation increments the cursor to the next line.
         * Ensure there is data available before calling this function.
         * @return The measurement as a string.
         */
        String ReadMeasure();

        /**
         * Check if there are more lines available to read in the file.
         * @return True if there is more data to read; false otherwise.
         * Note: Always call this before using ReadMeasure() to prevent errors.
         */
        bool IsDataAvailable();

        /**
         * Clean up resources when the Reader is no longer needed.
         * Closes the file and resets the cursor position.
         */
        void Dispose();
};

// Include the implementation of the Reader class
#include "Reader.cpp"

#endif // READER_CLASS_H
