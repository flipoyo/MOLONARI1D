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
#include <MKRWAN.h>

LoRaModem modem;
std::queue<String> sendingQueue;
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

void PrintQueue(std::queue<String> &receiveQueue)
{
  LOG_LN("Session ended. Printing all received data:");
  while (!receiveQueue.empty())
  {
    delay(500);
    LOG_LN(receiveQueue.front()); // Print the front item in the queue
    receiveQueue.pop();           // Remove item from the queue
  }
  LOG_LN("All data printed. Queue is now empty.");
}

bool SendQueue()
{

  LOG_LN("Session ended. Sending to the server all received data:");
  while (!sendingQueue.empty())
  {
    Serial.print("Sent: ");

    String payload = sendingQueue.front();
    int err;
    int counter = 0;
    do
    {
      counter++;
      modem.beginPacket();
      modem.print(payload);
      err = modem.endPacket(true);
      if (err <= 0)
      {
        Serial.println("Error in sending !");
        delay(10000);
      }
      if (counter == 6)
        return false;
    } while (err <= 0);
    delay(10000);
    LOG_LN(payload);    // Print the front item in the queue
    sendingQueue.pop(); // Remove item from the queue
  }
  LOG_LN("All data sended. Queue is now empty.");
  return true;
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
    int last = lora.receivePackets(receiveQueue);
    lora.closeSession(last);

    lora.stopLoRa();
    //PrintQueue(receiveQueue);
     while (!receiveQueue.empty()) {
        sendingQueue.push(receiveQueue.front());  // Add elements to mainQueue
        receiveQueue.pop();                    // Remove them from tempQueue
    }
    
    rotate++;
    if (rotate == 1)
    {
      rotate = 0;

      while (!SetUpLoRaWAN())
      {
        Serial.println("Error in initialization of LoRaWAN");
        delay(10000);
      }
      SendQueue();

      waiter.sleepUntil(60000);

    }
  }
}

bool SetUpLoRaWAN()
{
  // Enter the appEUI  and appKey from the TTN server
  String appEui = "0000000000000000";
  String appKey = "387BC5DEF778168781DDE361D4407953";
  // change this to your regional band (eg. US915, AS923, ...)
  if (!modem.begin(EU868))
  {
    Serial.println("Failed to start module");
    return false;
  };
  int connected = modem.joinOTAA(appEui, appKey);
  if (!connected)
  {
    Serial.println("Something went wrong; are you indoor? Move near a window and retry");
    return false;
  }
  int err;
  modem.minPollInterval(60);
  modem.setADR(true);
  do
  {
    modem.beginPacket();
    modem.print("Start Sending ...");
    err = modem.endPacket(true);
    delay(8000);
  } while (err <= 0);
  return true;
}
