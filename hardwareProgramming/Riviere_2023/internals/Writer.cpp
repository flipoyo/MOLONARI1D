

// Check that the file has not been imported before
#ifndef WRITER_CLASS
#define WRITER_CLASS

#include "Writer.hpp"
#include "Time.cpp"
#include <String.h>


#ifdef SD_DEBUG
#define SD_LOG_LN(msg) Serial.println(msg)
#else
#define SD_LOG_LN(msg)
#endif


const String coma = String(',');

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


void GetCurrentTime(Measure* measure) {
    // Not implemented yet.
    GetCurrentHour().toCharArray(measure->time, 9);
    GetCurrentDate().toCharArray(measure->date, 11);
}

//Class methods

void Writer::WriteInNewLine(Measure data){
    
    SD_LOG_LN("Writing data ...");
    this->file.println(String(data.id)+ coma + data.date + coma + data.time + coma + String(data.mesure1) + coma + String(data.mesure2) + coma + String(data.mesure3) + coma + String(data.mesure4));
    SD_LOG_LN("Done");

    SD_LOG_LN("Flushing ...");
    this->file.flush();
    SD_LOG_LN("Done");
}

void Writer::ConvertToWriteableMeasure(Measure* measure, MEASURE_T mesure1, MEASURE_T mesure2, MEASURE_T mesure3, MEASURE_T mesure4) {
    measure->mesure1 = mesure1;
    measure->mesure2 = mesure2;
    measure->mesure3 = mesure3;
    measure->mesure4 = mesure4;
}

void Writer::Reconnect() {
    this->file.close();
    this->file = SD.open(filename, FILE_WRITE);
}

void Writer::EstablishConnection() {
    this->next_id = GetNextLine();
    this->file = SD.open(filename, FILE_WRITE);
}

void Writer::LogData(MEASURE_T mesure1, MEASURE_T mesure2, MEASURE_T mesure3, MEASURE_T mesure4) {

    // Create a new Measure
    Measure data;
    this->ConvertToWriteableMeasure(&data, mesure1, mesure2, mesure3, mesure4);
    GetCurrentTime(&data);
    data.id = this->next_id;

    if (!this->file){
        SD_LOG_LN("SD connection lost.");
        SD_LOG_LN("Trying to reconnect ...");

        this->Reconnect();
        delay(10);

        if (!this->file){
            SD_LOG_LN("Connection could not be established back.");
            return;
        }
    }
    
    this->WriteInNewLine(data);
    this->next_id++;
}

void Writer::Dispose() {
    this->file.close();
}

#endif