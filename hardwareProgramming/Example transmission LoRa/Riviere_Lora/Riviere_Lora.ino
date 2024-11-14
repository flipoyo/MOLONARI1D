#include "internals/Lora.hpp"
#include <queue> // Using standard library queue

uint8_t MyAddress = 0xcc;
uint8_t RelayAdd = 0xaa;

void setup()
{
  // Enable the built-in LED during initialization
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialize Serial
  Serial.begin(9600);
  // Wait up to 5 seconds for serial to connect
  unsigned long end_date = millis() + 5000;
  while (!Serial && millis() < end_date)
  {
    // Waiting for Serial
  }

  // Disable the built-in LED after initialization
  // digitalWrite(LED_BUILTIN, LOW);

  // Serial.println("Initialization complete!");
  // Serial.println("Waiting to start communication...");
}

std::queue<String> loadDataIntoQueue(int shift)
{
  std::queue<String> Queue;
  for (int i = 100 - shift; i <= 280; i++)
  {
    String line = "hellor from riviere" + String(i+1);
    Queue.push(line);
    if (Queue.size() >= 200)
      break; // Limit queue size if necessary
  }
  return Queue;
}

LoraCommunication lora(868E6, MyAddress, RelayAdd);

void loop()
{
  Serial.println("Starting new communication session...");
  lora.startLoRa();
  int shift = 0;
  if (lora.performHandshake(shift))
  {
    std::queue<String> sendQueue = loadDataIntoQueue(shift);
    uint8_t last = lora.sendPackets(sendQueue);
    lora.closeSession(last);
  }

  lora.stopLoRa();
  delay(10000);
}
