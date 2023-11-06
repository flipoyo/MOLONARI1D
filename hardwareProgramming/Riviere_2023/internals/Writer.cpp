#include <SD.h>
#include <SPI.h>
#include <String.h>
#include "Measure.h"
#include "Writer.h"

const char filename[] = "datalog.csv";


Writer::Writer(/* args */)
{
    dataFile = SD.open(filename, FILE_WRITE);
}

Writer::~Writer()
{
    dataFile.close();
}

void Writer::WriteInNewLine(File* file, Measure data){
    file->print(data.id);
    file->print(",");
    file->print(data.date);
    file->print(",");
    file->print(data.time);
    file->print(",");
    file->print(data.mesure1);
    file->print(",");
    file->print(data.mesure2);
    file->print(",");
    file->print(data.mesure3);
    file->print(",");
    file->println(data.mesure4);
}