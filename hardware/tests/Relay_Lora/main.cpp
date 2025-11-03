//FORMERLY NAMED Relay_Lora.ino

/*#ifndef BUILDPATH
#define BUILDPATH (relative_path) "../" + relative_path
#endif

/ This is a small, focused test script using the LoraCommunication class,
   simulating scenarios with non-real data to quickly debug and refine the protocol
   without deploying the entire system. /

#include BUILDPATH("../../field_code/libs/shared/protocols/LoRa/Lora.hpp")
*/
#include <queue>

#include<Arduino.h>
#include<SPI.h>
//#include "Lora.hpp" //WARNING : doesn't match with this adress but with build directory path that must be specified in arduino CLI build line.


// Uncomment this line to enable diagnostics log on serial for the main loop
#define DEBUG
// Uncomment this line to enable diagnostics log on serial for LoRa operations
// #define LORA_DEBUG

#ifdef DEBUG
#define LOG(x) Serial.print(x)     // Macro for logging without a newline
#define LOG_LN(x) Serial.println(x) // Macro for logging with a newline
#else
#define LOG(x)                     // Empty macros when debugging is disabled
#define LOG_LN(x)
#endif

// Define the device's own address
uint8_t MyAddres = 0xaa;
// Default destination address, used when no specific destination is set
uint8_t defaultdestination = 0xff;
// Counter to rotate through test modes or other options (if applicable)
uint8_t rotate = 0;
main(){

}
void setup() {
  // Configure the built-in LED as output
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // Turn the LED on for setup indication

  // Initialize Serial communication for debugging
  Serial.begin(115200);
  // Wait up to 5 seconds for the Serial connection to establish
  unsigned long end_date = millis() + 5000;
  while (!Serial && millis() < end_date) {
    // Do nothing while waiting
  }

  // Configure the built-in LED for pull-down mode
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);

  // Log that the receiver is ready
  Serial.println("Receiver ready...");
}

// Function to print all the data in the queue
void PrintQueue(std::queue<String> &receiveQueue)
{
  LOG_LN("Session ended. Printing all received data:");
  // Loop through the queue and print each message
  while (!receiveQueue.empty())
  {
    delay(500); // Small delay to allow for Serial printing
    Serial.println(receiveQueue.front()); // Print the front item in the queue
    receiveQueue.pop();                   // Remove the item from the queue
  }
  LOG_LN("All data printed. Queue is now empty.");
}
/*
// ----- Main loop -----
void loop()
{
  Waiter waiter;          // Initialize a Waiter object (assumed to manage timing)
  waiter.startTimer();    // Start the timer for measuring session duration
  
  lora.setdesttodefault(); // Reset destination address to default before starting

  // Queue to store received data
  std::queue<String> receiveQueue;

  lora.startLoRa(); // Start the LoRa communication session
  
  if (lora.Handshake(0)) // Perform handshake with sensors or other devices
  {
    LOG_LN("----------- Handshake done ----------");
    
    // Receive packets and store them in the receive queue
    int last = lora.receivePackets(receiveQueue);
    
    // Close the LoRa session, passing the last packet index
    lora.closeSession(last);

    lora.stopLoRa(); // Stop the LoRa module
    LOG_LN("----------- LoRa Stopped ------------");
    
    // Print all the received data
    PrintQueue(receiveQueue);

    // Increment the rotation counter and reset after 3
    rotate++;
    if (rotate == 3)
    {
      rotate = 0;
    }
  }
}
*/