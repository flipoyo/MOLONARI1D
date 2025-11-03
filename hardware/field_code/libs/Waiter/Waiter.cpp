#include <queue>
#include <Arduino.h>
#include <ArduinoLowPower.h>

#include "Waiter.hpp"
#include "Reader.hpp"
#include "LoRa_Molonari.hpp"
#include "Time.hpp"

#define DEBUG
#ifdef DEBUG
#define DEBUG_WAITER
#endif
#ifdef DEBUG_WAITER
#define DEBUG_LOG(msg) Serial.println(msg)
#define DEBUG_LOG_NO_LN(msg) Serial.print(msg)
#else
#define DEBUG_LOG(msg) 
#define DEBUG_LOG_NO_LN(msg)
#endif

// PrintQueue function definition
void PrintQueue(std::queue<String> &receiveQueue) {
    DEBUG_LOG("Session ended. Printing all received data:");
    while (!receiveQueue.empty()) {
        DEBUG_LOG(receiveQueue.front()); // Show the first item in the queue
        receiveQueue.pop();                   // Remove the printed item
    }
    DEBUG_LOG("All data printed. Queue is now empty.");
}

// Default constructor
Waiter::Waiter() {}

// Sleep the Arduino until the desired waiting time passes
void Waiter::sleepUntil(long wainting_interval) {

    DEBUG_LOG("Sleeping for " + String(wainting_interval) + " ms");
    // Sleep for the calculated time
    unsigned long waiting_interval_unsigned = uint32_t(wainting_interval);
    LowPower.deepSleep(waiting_interval_unsigned); //Conversion rendue nécessaire par l'implémentation de deepSleep dans la librairie arduino
}
