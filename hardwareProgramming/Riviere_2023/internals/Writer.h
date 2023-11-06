// Check that the file has not been imported before
#ifndef WRITER_CLASS_H
#define WRITER_CLASS_H

class Writer
{
    private:
        unsigned int next_id;

        // Append a Measure to the csv file.
        void WriteInNewLine(Measure data);

        // Convert the raw data into a Measure.
        void ConvertToWriteableMeasure(Measure* measure, unsigned int raw_measure[4]);

    public:
        void EstablishConnection();

        // Process and append raw data to the csv file.
        void LogData(unsigned int raw_measure[4]);
        // void LogData(unsigned int raw_measure[2]);

        // ~Writer();
};

#include "Writer.cpp"

#endif