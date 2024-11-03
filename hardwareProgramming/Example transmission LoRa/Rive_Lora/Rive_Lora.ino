#include "internals/Lora.hpp"
#include <queue>

uint8_t rotate = 0;
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialise Serial
  Serial.begin(115200);
  // Wait up to 5 seconds for serial to connect
  unsigned long end_date = millis() + 5000;
  while (!Serial && millis() < end_date) {
    // Do nothing
  }

  pinMode(LED_BUILTIN, INPUT_PULLDOWN);
  Serial.println("Receiver ready...");
}

void PrintQueue(std::queue<String> receiveQueue;) {
  Serial.println("Session ended. Printing all received data:");
  while (!receiveQueue.empty()) {
    Serial.println(receiveQueue.front());  // Print the front item in the queue
    receiveQueue.pop();                    // Remove item from the queue
  }
  Serial.println("All data printed. Queue is now empty.");
}

void loop() {
  // localAddress = 0xaa;
  
  LoraCommunication lora(868E6, 0xaa , 0xff);
  std::queue<String> receiveQueue;
  lora.startLoRa();
  if (performHandshake(rotate*20)){
    int last = receivePackets(receiveQueue)
    closeSession(last);
  }
  lora.stopLoRa();
  PrintQueue(receiveQueue);
  rotate=rotate ^ 1;
  
}
