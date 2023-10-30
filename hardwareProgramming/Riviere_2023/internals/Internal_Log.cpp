// This file will contain all the code to log the data internally before they get transmitted.
// It uses an internal memory of the MKR board : 2MByte of persistent flash memory.

#include <FlashStorage.h>
#include "Measure.h"
#include "testSample.h"
#include "InternalData.h"

// Reserve a portion of flash memory to store a Measure.
FlashStorage(flashData, InternalData);

unsigned int GetAvailableMemory(InternalData internalData) {
  unsigned int lenthOfArray = sizeof(internalData.data)/sizeof(Measure);
  return lenthOfArray - internalData.nbOfMeasures;
}

// Display a Measure on the Serial monitor.
void DisplayMeasure(Measure newData) {
  Serial.print("Date: ");
  Serial.println(newData.date);
  Serial.print("Capteur1: ");
  Serial.println(newData.mesure1);
  Serial.print("Capteur2: ");
  Serial.println(newData.mesure2);
  Serial.print("Capteur3: ");
  Serial.println(newData.mesure3);
  Serial.print("Capteur4: ");
  Serial.println(newData.mesure4);

}

// Display all the data stored in the internal memory.
void DisplayFlashMemory() {
  // Read the current Flash memory
  InternalData internalData = flashData.read();

  Serial.println("Number of measures stored in Flash memory so far:");
  Serial.println(internalData.nbOfMeasures);

  for (int i = 0; i < internalData.nbOfMeasures; i++) {
    Serial.println();
    Serial.print("Measure number :");
    Serial.println(i+1);
    DisplayMeasure(internalData.data[i]);
  }
  flashData.write(internalData);
}

void DisplayMemoryState(InternalData internalData){
  if (Serial) {
    Serial.println("-------------MEMORY-STATE-----------------------");
    Serial.println("Data stored in Flash memory so far:");
    Serial.println(internalData.nbOfMeasures);
    Serial.println("Number of available memory slots:");
    Serial.println(internalData.availableMemory);
    Serial.println("------------------------------------------------");
  }
}

// Convert a testSample to a Measure.
Measure ConvertToWritableData(testSample rawData) {
  Measure formattedData;
  formattedData.valid = true;
  strncpy(formattedData.date,rawData.date,21);
  formattedData.mesure1 = rawData.mesure1;
  formattedData.mesure2 = rawData.mesure2;
  formattedData.mesure3 = rawData.mesure3;
  formattedData.mesure4 = rawData.mesure4;
  return formattedData;
}

void InitialiseLog() {
  // Read the current Flash memory
  InternalData internalData = flashData.read();

  // Initialize the Flash memory if it is the first time the board is used.
  if (internalData.nbOfMeasures == 0) {
    Serial.println("Hello There ! This device's empty and ready to store some data.");
    internalData.availableMemory = GetAvailableMemory(internalData);
  }

  //In the cas there are some mesure, give them to the user
  else {
    Serial.println("Hello Back ! There are some data stored in the Flash memory.");
    DisplayMemoryState(internalData);
  }

  flashData.write(internalData);
}

// Log the data in the internal memory.
void LogData(testSample rawData) {
  // Read the current Flash memory
  InternalData internalData = flashData.read();

  if (internalData.availableMemory > 0) {
    // Create a new Measure instance
    Measure newData;
    newData = ConvertToWritableData(rawData);

    // Get the number of measures already stored
    int nbOfMeasures = internalData.nbOfMeasures;
    
    //Append the last measure to the new data
    internalData.data[nbOfMeasures] = newData;
    internalData.nbOfMeasures++;
    internalData.availableMemory--;
  }

  else if (Serial) {
    Serial.println("No more memory available.");
  }

  // Write the new data in Flashs
    flashData.write(internalData);

    DisplayMemoryState(internalData);
}