#include "internals/Lora.hpp"
#include <queue>

uint8_t MyAddres = 0xaa;
uint8_t defaultdestination = 0xff;
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

void PrintQueue(std::queue<String> &receiveQueue)
{
  LOG_LN("Session ended. Printing all received data:");
  while (!receiveQueue.empty())
  {
    delay(500);
    Serial.println(receiveQueue.front()); // Print the front item in the queue
    receiveQueue.pop();           // Remove item from the queue
  }
  LOG_LN("All data printed. Queue is now empty.");
}

// ----- Main loop -----

void loop()
{
  Waiter waiter;
  waiter.startTimer();
  lora.setdesttodefault();
  std::queue<String> receiveQueue;
  lora.startLoRa();
  if (lora.Handshake(0))
  {
    LOG_LN("-----------Handshake done----------");
    int last = lora.receivePackets(receiveQueue);
    lora.closeSession(last);

    lora.stopLoRa();
    LOG_LN("-----------Lora Stop------------");
    PrintQueue(receiveQueue);

    
    rotate++;
    if (rotate == 3)
    {
      rotate = 0;
    }
  }
}
