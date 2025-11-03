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

    // Log the waiting time for debugging
    Serial.println("Sleeping for " + String(time_to_wait) + " ms");

    // Sleep for the calculated time
    LowPower.deepSleep(time_to_wait);
}


// Wait without sleeping to handle other tasks // cette fonction n'est jamais utilisée et doit etre supprimée
void Waiter::delayUntil(uint32_t desired_waiting_time, int role) {
    unsigned long end_date = starting_time + desired_waiting_time;

    // Loop until the time is up
    while (GetSecondsSinceMidnight() < end_date) {
        Serial.println("Starting new communication session...");

        // Set up LoRa communication
        LoraCommunication lora(868E6, String(0xbb), String(0xaa), static_cast<RoleType>(role));
        Reader reader;
        lora.startLoRa();
        uint8_t shift = 0;

        // Perform handshake and connect to the reader
        bool handshake = lora.handshake(shift);
        bool readerConnected = reader.EstablishConnection(shift);

        // If everything works, send the data
        if (handshake && readerConnected) {
            std::queue<String> sendQueue = reader.loadDataIntoQueue();
            int nbofACK = lora.sendPackets(sendQueue);

            // Update the cursor and close session
            reader.UpdateCursor(nbofACK);
            lora.closeSession(nbofACK);

            // Clean up
            lora.stopLoRa();
            reader.Dispose();

            return; // Exit since the task is done
        }

        // Clean up and retry on failure
        lora.stopLoRa();
        reader.Dispose();

        delay(1); // Small delay to prevent the loop from running too fast
    }
}
