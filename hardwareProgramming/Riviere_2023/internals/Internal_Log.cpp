// This file will contain all the code to log the data internally before they get transmitted.
// It uses an internal memory of the MKR board : 2MByte of persistent flash memory.

#include <SD.h>
#include <SPI.h>
#include "Measure.h"
#include "testSample.h"

const int CSpin = 6;
const char filename[] = "datalog.csv";
const char header[] = "Id,Date,Time,Capteur1,Capteur2,Capteur3,Capteur4";

// Display a Measure on the Serial monitor.
void DisplayMeasure(Measure measure) {
  Serial.print("Id: ");
  Serial.println(measure.id);	
  Serial.print("Date: ");
  Serial.println(measure.date);
  Serial.print("Time: ");
  Serial.println(measure.time);
  Serial.print("Capteur1: ");
  Serial.println(measure.mesure1);
  Serial.print("Capteur2: ");
  Serial.println(measure.mesure2);
  Serial.print("Capteur3: ");
  Serial.println(measure.mesure3);
  Serial.print("Capteur4: ");
  Serial.println(measure.mesure4);

}

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
      Serial.println("No connection established with the SD card.");
      return false;
    }

    else if (!isAlreadyInitialised()) {
        File dataFile = SD.open(filename, FILE_WRITE);
        if (dataFile) {
            dataFile.println(header);
            Serial.println("The file has been intitialized.");
        }
        dataFile.close();
    }
    else {
      Serial.println("The file already exists.");
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

void ConvertToWriteableMeasure(Measure* measure, unsigned int raw_measure[4]) {
    measure->mesure1 = raw_measure[0];
    measure->mesure2 = raw_measure[1];
    measure->mesure3 = raw_measure[2];
    measure->mesure4 = raw_measure[3];
}

void GetCurrentTime(Measure* measure) {
    // Get the current time
    // unsigned long epochTime = rtc.getEpoch();
    // Print the current time
    // String currentTime = rtc.formatTime("H:i:s", epochTime);
    // String currentDate = rtc.formatTime("d/m/Y", epochTime);
    // currentTime.toCharArray(measure->time, 9);
    // currentDate.toCharArray(measure->date, 11);

    strncpy(measure->time, "12:00:00", 9);
    strncpy(measure->date, "01/01/2020", 11);
}

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

Measure GetMeasurementById(unsigned int id) {
  // myFile = SD.open(filename);
  // if (myFile) {
  //   line = 
  //   while (myFile.available()) {
  //     // read an entire csv line (which end is a \n)
  //     line = myFile.readStringUntil('\n');
  //   }
  // }

  // myFile.close();
}