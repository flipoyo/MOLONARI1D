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
    Serial.println("Session ended. Printing all received data:");
    while (!receiveQueue.empty()) {
        Serial.println(receiveQueue.front()); // Show the first item in the queue
        receiveQueue.pop();                   // Remove the printed item
    }
    Serial.println("All data printed. Queue is now empty.");
}

// Default constructor
Waiter::Waiter() {}

// Start tracking time
void Waiter::startTimer() {
    starting_time = GetSecondsSinceMidnight();
}

// Sleep the Arduino until the desired waiting time passes
void Waiter::sleepUntil(unsigned long desired_waiting_time) {

    //modifier cette fonction : pourquoi cet ajustement et ne pas juste faire dormir desiredWaitingTime ??
    unsigned long time_to_wait = (starting_time + desired_waiting_time) - GetSecondsSinceMidnight();

    Serial.println("Sleeping for " + String(time_to_wait) + " ms");

    LowPower.deepSleep(time_to_wait);
}

