#include <FlashStorage.h>
#include "Measure.h"

FlashStorage(flashData, /*Set of Measures*/);

// The exact signature of this function has to be determined
void GetData() {
  // Read the last written data from Flash
  Measure lastData = flashData.read();
  Serial.println("Data stored in Flash memory so far:");
  Serial.println();
}

void DeleteFlashMemory() {
  flashData.erase();
}

void AskDeleteFlashMemory() {
  // Display a message for the user to ask if he wants to delete the data
    // If the user wants to delete the data, call DeleteFlashMemory()

}