#include "Measure.h"

// Check that the file has not been imported before
#ifndef WRITER_CLASS_H
#define WRITER_CLASS_H

class Writer
{
    private:
        File file; 
        unsigned int next_id;

        // Append a Measure to the csv file.
        void WriteInNewLine(Measure data);

        // Convert the raw data into a Measure.
        void ConvertToWriteableMeasure(Measure* measure, MEASURE_T mesure1, MEASURE_T mesure2, MEASURE_T mesure3, MEASURE_T mesure4);

        // Reconnect to the SD card.
        void Reconnect();
    public:
        // Establish the connection with the SD card.
        void EstablishConnection();

        // Process and append raw data to the csv file.
        void LogData(MEASURE_T mesure1, MEASURE_T mesure2 = 0, MEASURE_T mesure3 = 0, MEASURE_T mesure4 = 0);

        // Close the connection with the SD card.
        void Dispose();
};

#include "Writer.cpp"

#endif