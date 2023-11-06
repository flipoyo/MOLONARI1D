// Check that the file has not been imported before
#ifndef WRITER_CLASS
#define WRITER_CLASS

class Writer
{
    private:
        File file;

    public:
        Writer();
        
        // Append a Measure to the csv file.
        void WriteInNewLine(Measure data);

        ~Writer();
};

#include "Writer.cpp"