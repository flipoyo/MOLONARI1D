/*
This firmware will be is meant for the LoRa relay in the Molonari system.

Functionalities :
  - Request measurements from the sensors
  - Print the measurements on the serial port

In long term, this firmware will be able to :
  - Send the measurements to the server

Required hardware :
 - Arduino MKR WAN 1310
*/

// ----- Settings -----

// Define the data-type of a measurement
#define MEASURE_T double

// Uncomment this line to enable dignostics log on serial about the main loop
#define DEBUG
// Uncomment this line to enable diagnostics log on serial for lora operations
// #define LORA_DEBUG

#ifdef DEBUG
#define LOG(x) Serial.print(x)
#define LOG_LN(x) Serial.println(x)
#else
#define LOG(x)
#define LOG_LN(x)
#endif

// ----- Dependencies -----

#include "internals/Lora.hpp"
#include "internals/Waiter.hpp"

uint8_t MyAddres = 0xaa;
uint8_t defaultdestination = 0xff;
uint8_t rotate = 0;
LoraCommunication lora(868E6, MyAddres, defaultdestination);
// ----- Main Setup -----

void setup()
{
  // Enable the builtin LED during initialisation
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialise serial
  Serial.begin(115200);

  // Wait for connection to start
  while (!Serial)
  {
    // Do nothing
  }
  LOG_LN("LoRa relay for Molonari system");
  LOG_LN("See : https://github.com/flipoyo/MOLONARI1D");
  LOG_LN("");

  // Disable the builtin LED
  digitalWrite(LED_BUILTIN, LOW);
}

void PrintQueue(std::queue<String> receiveQueue)
{
  LOG_LN("Session ended. Printing all received data:");
  while (!receiveQueue.empty())
  {
    LOG_LN(receiveQueue.front()); // Print the front item in the queue
    receiveQueue.pop();           // Remove item from the queue
  }
  LOG_LN("All data printed. Queue is now empty.");
}

// ----- Main loop -----

void loop()
{
  Waiter waiter;
  waiter.startTimer();
  // Request measurement
  lora.setdesttodefault();
  std::queue<String> receiveQueue;
  lora.startLoRa();
  if (lora.Handshake(0))
  {
    int last = lora.receivePackets(receiveQueue);
    lora.closeSession(last);

    lora.stopLoRa();
    PrintQueue(receiveQueue);
    rotate = rotate % 3;
    rotate++;
    if (rotate == 3)
      waiter.sleepUntil(300000);
  }
}
