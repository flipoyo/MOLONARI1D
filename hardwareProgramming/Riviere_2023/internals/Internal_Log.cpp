// This file will contain all the code to log the data internally before they get transmitted.
// It uses an internal memory of the MKR board : 2MByte of persistent flash memory.

#include <SD.h>
#include <SPI.h>
#include <String.h>
#include "Measure.h"


// Check that the file has not been imported before
#ifndef INTERNAL_LOG
#define INTERNAL_LOG


const int CSpin = 6;
const char filename[] = "datalog.csv";
const char header[] = "Id,Date,Time,Capteur1,Capteur2,Capteur3,Capteur4";


bool isAlreadyInitialised() {
    File file =  SD.open(filename);
    if (!file) {
      return false;
    }
    else{
      return file.read() != -1;
    }
    file.close();
}

//Generate a CSV file with a header IF necessary.
bool InitialiseLog() {
    if (!SD.begin(CSpin)) {
      return false;
    }

    else if (!isAlreadyInitialised()) {
        File dataFile = SD.open(filename, FILE_WRITE);
        if (dataFile) {
            dataFile.println(header);
        }
        dataFile.close();
    }

    return true;
}

// Write a Measure in a new line of the file.
void WriteInNewLine(File* file, Measure data){
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

// Convert the raw data into a Measure.
void ConvertToWriteableMeasure(Measure* measure, unsigned int raw_measure[4]) {
    measure->mesure1 = raw_measure[0];
    measure->mesure2 = raw_measure[1];
    measure->mesure3 = raw_measure[2];
    measure->mesure4 = raw_measure[3];
}

// TODO : Get the current time from the RTC. (not necessarly here)
void GetCurrentTime(Measure* measure) {
    // Not implemented yet.
    strncpy(measure->time, "12:00:00", 9);
    strncpy(measure->date, "01/01/2020", 11);
}

// Get the last id in [filename].csv, which is the number of lines - 1 (because of the header line).
unsigned int GetLastMeasurementId() {
  File file = SD.open(filename);
  unsigned int number_of_lines = 0;
  if (file) {
    while (file.available()) {
      // read an entire csv line (which end is a \n)
      if (file.read() == '\n') {
        number_of_lines++;
      }
    }
  }
  return number_of_lines - 1; //which is the last id
}

// Log the data in the internal memory.
void LogData(unsigned int raw_measure[4]) {

    // Create a new Measure
    Measure data;
    ConvertToWriteableMeasure(&data, raw_measure);
    GetCurrentTime(&data);
    data.id = GetLastMeasurementId() + 1;
    
    File file = SD.open(filename, FILE_WRITE);
    if (file) {
      WriteInNewLine(&file, data);
    }

    file.close();
}

// Convert a CSV line (Arduino String Type= into a Measure.
Measure StringToMeasure(String line){
  Measure measure;
  String delimiter = ",";
  String token;
  line.concat(delimiter);
  int i = 0;
  int pos = 0;
  while ((pos = line.indexOf(delimiter)) != -1) {
    token = line.substring(0, pos);
    switch (i)
    {
    case 0:
      measure.id = token.toInt();
      break;
    case 1:
      strncpy(measure.date, token.c_str(), 11);
      break;
    case 2:
      strncpy(measure.time, token.c_str(), 9);
      break;
    case 3:
      measure.mesure1 = token.toInt();
      break;
    case 4:
      measure.mesure2 = token.toInt();
      break;
    case 5:
      measure.mesure3 = token.toInt();
      break;
    case 6:
      measure.mesure4 = token.toInt();
      break;
    default:
      break;
    }
    line.remove(0, pos + delimiter.length());
    i++;
  }
  return measure;
}

// Get a Measure by its id in [filename].
Measure GetMeasurementById(unsigned int id) {
  File file = SD.open(filename);
  unsigned int current_id = 0;

  if (file) {
    while (file.available()) {
      
      if (current_id == id) {
          Measure measure = StringToMeasure(file.readStringUntil('\n'));
        return measure;
      }

      else {
        file.readStringUntil('\n');
        current_id++;
      }
    }
  }
  file.close();
}


#endif