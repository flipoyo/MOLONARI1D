// This file will contain all the code to log the data internally before they get transmitted.
// It uses an internal memory of the MKR board : 2MByte of persistent flash memory.

#include <FlashStorage.h>
#include "Measure.h"
#include "testSample.h"

// Reserve a portion of flash memory to store a Measure.
FlashStorage(flashData, Measure);


// Initialise the log module for the first time.
void InitialiseLog(/* Parameters */) {
  Serial.begin(9600);
}

void DisplayMeasure(Measure newData, int writeIndex) {
  if (writeIndex > 0) {
    Serial.print("New data written at index ");
    Serial.println(writeIndex);
    }
  // Serial.print("Date: ");
  // Serial.println(newData.date);
  Serial.print("Capteur1: ");
  Serial.println(newData.mesure1);
  Serial.print("Capteur2: ");
  Serial.println(newData.mesure2);
  Serial.print("Capteur3: ");
  Serial.println(newData.mesure3);
  Serial.print("Capteur4: ");
  Serial.println(newData.mesure4);

}

Measure ConvertToWritableData(testSample rawData) {
  Measure formattedData;
  //Todo
  formattedData.valid = true;
  formattedData.mesure1 = rawData.mesure1;
  formattedData.mesure2 = rawData.mesure2;
  formattedData.mesure3 = rawData.mesure3;
  formattedData.mesure4 = rawData.mesure4;
  return formattedData;
}

// The exact signature of this function has to be determined
void LogData(testSample rawData) {
  // Create a new Measure instance
  Measure newData;
  newData = ConvertToWritableData(rawData);

  
  // Read the last written data from Flash
  Measure lastData;
  lastData = flashData.read();

  if (lastData.valid) {
    Serial.println("Last data written:");
    DisplayMeasure(lastData, 0);
    
  }
  else {
    Serial.println("No data written yet");
  }
  
  flashData.write(newData);
  // DisplayWhatHappened(lastData, writeIndex);
  // DisplayWhatHappened(newData, writeIndex);
}

// The exact signature of this function has to be determined
void GetData(/* Parameters */) {
  // Todo
}