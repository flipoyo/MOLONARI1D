#include "internals/Lora.hpp"
//#include "internals/Reader.hpp"
//#include "internals/SD_Initializer.cpp"
#include <queue>  // Using standard library queue


//Reader dataReader; 
//const int CSPin = 5;
//const char filename[] = "RIVIERE.CSV";
void setup(){
  // Enable the builtin LED during initialisation
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialise Serial
  Serial.begin(115200);
  // Wait up to 5 seconds for serial to connect
  unsigned long end_date = millis() + 5000;
  while (!Serial && millis() < end_date) {
    // Do nothing
  }

  /*// Initialise SD Card
  Serial.print("Initialising SD card ...");
  bool success = InitialiseLog(CSPin);
  if (success) {
    Serial.println(" Done");
  } else {
    Serial.println(" Failed");
    noInterrupts();
    while (true) {}
  }*/

  //dataReader.EstablishConnection(0);  // Start reading from the file, line_cursor will be preserved
  

  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);

  Serial.println("Initialisation complete !");
  
  Serial.println("Waiting to start communication...");
}

std::queue<String> loadDataIntoQueue(int shift) {
  std::queue<String> Queue;
  for(int i = 100 - shift; i <= 280 ;i++) {
    String line = "hellor from riviere" + String(i);
    Queue.push(line);
    if (Queue.size() >= 300) break;  // Limit queue size if necessary
  }
  return Queue;
}


void loop() {
  Serial.println("Starting new communication session...");
  LoraCommunication lora(868E6, 0xbb , 0xaa);
  lora.startLoRa();
  int shift = 0;
  if (lora.performHandshake(shift)) {
    std::queue<String> sendQueue = loadDataIntoQueue(shift); 
    lora.sendPackets(sendQueue);
  }

  lora.stopLoRa();
  delay(10000);
}

