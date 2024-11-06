// This file defines the Writer class, which is used to write a serie of measurements to a CSV file.
// See internals/Writer.hpp for the definitions.

// Check that the file has not been imported before
#ifndef WRITER_CLASS
#define WRITER_CLASS

#include "Writer.hpp"
#include "Time.cpp"

#include <String.h>
#include <SD.h>

#ifdef SD_DEBUG
#define SD_LOG(msg) Serial.print(msg)
#define SD_LOG_LN(msg) Serial.println(msg)
#else
#define SD_LOG(msg)
#define SD_LOG_LN(msg)
#endif


const String COMA = String(',');

// Search for the number of lines in the csv file->
// SHOULD BE CALLED ONLY ONCE.
unsigned int GetNextLine() {
  // Todo : Now, the function counts the number of lines. It would be more stable if it got the index of the last measurement.

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


void ApplyCurrentTime(Measure* measure) {
    GetCurrentHour().toCharArray(measure->time, 9);
    GetCurrentDate().toCharArray(measure->date, 11);
}

//Class methods

void Writer::WriteInNewLine(Measure data){
    
    SD_LOG("Writing data ...");
    this->file.println(String(data.id)+ COMA + data.date + COMA + data.time + COMA + String(data.chanel1) + COMA + String(data.chanel2) + COMA + String(data.chanel3) + COMA + String(data.chanel4));
    SD_LOG_LN(" Done");

    SD_LOG("Flushing ...");
    this->file.flush();
    SD_LOG_LN(" Done");
}

void Writer::ApplyContent(Measure* measure, MEASURE_T mesure1, MEASURE_T mesure2, MEASURE_T mesure3, MEASURE_T mesure4) {
    measure->chanel1 = mesure1;
    measure->chanel2 = mesure2;
    measure->chanel3 = mesure3;
    measure->chanel4 = mesure4;
}

bool Writer::Reconnect() {
    this->file.close();
    if (!SD.begin(this->CSPin)) {
        return false;
    }
    this->file = SD.open(filename, FILE_WRITE);
    return this->file;
}

void Writer::EstablishConnection(const int CSpin) {
    this->CSPin = CSpin;
    this->next_id = GetNextLine();
    this->file = SD.open(filename, FILE_WRITE);
}

void Writer::LogData(MEASURE_T mesure1, MEASURE_T mesure2, MEASURE_T mesure3, MEASURE_T mesure4) {

    // Create a new Measure
    Measure data;
    this->ApplyContent(&data, mesure1, mesure2, mesure3, mesure4);
    ApplyCurrentTime(&data);
    data.id = this->next_id;

    // Check if the connection is still established
    bool is_connected = SD.begin(this->CSPin) && this->file;
    if (!is_connected) {
        SD_LOG_LN("SD connection lost.");
        SD_LOG_LN("Trying to reconnect ...");
        
        // Try to reconnect
        is_connected = this->Reconnect();
        if (!is_connected) {
            SD_LOG_LN("Connection could not be established.");
            return;
        }
    }

    if (is_connected) {
        this->WriteInNewLine(data);
    }
    this->next_id++;
}

void Writer::Dispose() {
    this->file.close();
}

#endif