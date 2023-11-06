#include <SD.h>
#include <SPI.h>
#include <String.h>
#include "Measure.h"
#include "Writer.h"

#ifndef WRITER_CLASS
#define WRITER_CLASS


// Search for the number of lines in the csv file->
// SHOULD BE CALLED ONLY ONCE.
unsigned int GetNextLine() {
  File readInfile = SD.open(filename);
  unsigned int number_of_lines = 0;
  if (readInfile) {
    while (readInfile.available()) {
      // read an entire csv line (which end is a \n)
      if (readInfile.read() == '\n') {
        number_of_lines++;
      }
    }
  }
  readInfile.close();
  return number_of_lines;
}

// TODO : Get the current time from the RTC. (not necessarly here)
void GetCurrentTime(Measure* measure) {
    // Not implemented yet.
    strncpy(measure->time, "12:00:00", 9);
    strncpy(measure->date, "01/01/2020", 11);
}

//Class methods

void Writer::WriteInNewLine(Measure data){
    File file = SD.open(filename, FILE_WRITE);

    file.print(data.id);
    file.print(",");
    file.print(data.date);
    file.print(",");
    file.print(data.time);
    file.print(",");
    file.print(data.mesure1);
    file.print(",");
    file.print(data.mesure2);
    file.print(",");
    file.print(data.mesure3);
    file.print(",");
    file.println(data.mesure4);

    file.close();
}

void Writer::ConvertToWriteableMeasure(Measure* measure, unsigned int raw_measure[4]) {
    measure->mesure1 = raw_measure[0];
    measure->mesure2 = raw_measure[1];
    measure->mesure3 = raw_measure[2];
    measure->mesure4 = raw_measure[3];
}

void Writer::EstablishConnection() {
    this->next_id = GetNextLine();
}

void Writer::LogData(unsigned int raw_measure[4]) {

    // Create a new Measure
    Measure data;
    this->ConvertToWriteableMeasure(&data, raw_measure);
    GetCurrentTime(&data);
    data.id = this->next_id;
    WriteInNewLine(data);

    this->next_id++;
}

// void Writer::LogData(unsigned int raw_measure[2]) {

//     //pre-format the raw data
//     unsigned int extended_raw_measure[4] = {raw_measure[0], raw_measure[1], 0, 0};

//     // Create a new Measure
//     Measure data;
//     this->ConvertToWriteableMeasure(&data, extended_raw_measure);
//     GetCurrentTime(&data);
//     data.id = this->next_id;
    
//     if (this->file) {
//       WriteInNewLine(data);
//     }

//     this->next_id++;
// }

#endif