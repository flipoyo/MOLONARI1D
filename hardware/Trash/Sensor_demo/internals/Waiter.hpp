// This file defines the Waiter class, which helps manage time efficiently in the Arduino loop.
// It includes low-power waiting and a way to ensure tasks run within a predictable time frame.

#ifndef WAITER_HPP
#define WAITER_HPP

#include <ArduinoLowPower.h>
#include "Reader.hpp"
#include "Low_Power.hpp"
#include "Lora.hpp"
#include <queue>

////////////
// Helper function to print the contents of a queue for debugging or logging
void PrintQueue(std::queue<String> &receiveQueue)
{
  Serial.println("Session ended. Printing all received data:");
  while (!receiveQueue.empty())
  {
    Serial.println(receiveQueue.front()); // Show the first item in the queue
    receiveQueue.pop();                   // Remove the printed item
  }
  Serial.println("All data printed. Queue is now empty.");
}
///////////

// Waiter class handles timed delays or sleeps while keeping the Arduino responsive to other tasks.
class Waiter
{
public:
    // Default constructor, no setup needed here
    Waiter() {}

    // Call this to start tracking time. It saves the current time for later calculations.
    void startTimer(){
        starting_time = millis();
    }

    // Put the Arduino to sleep in low-power mode for the remaining time until `desired_waiting_time` passes.
    void sleepUntil(unsigned long desired_waiting_time)
    {
        // Figure out how much time is left to wait
        unsigned long time_to_wait = (starting_time - millis()) + desired_waiting_time;

        // Log the waiting time for debugging
        Serial.println("Sleeping for " + String(time_to_wait) + " ms");
        
        // Sleep for the calculated time
        MyLowPower.Sleep(time_to_wait);
    }

    // Use this to wait without sleeping, so the Arduino can handle other tasks like LoRa communication.
    void delayUntil(unsigned long desired_waiting_time)
    {
        unsigned long end_date = starting_time + desired_waiting_time;
        
        // Keep looping until the time is up
        while (millis() < end_date)
        {
            Serial.println("Starting new communication session...");
            
            // Set up LoRa communication
            LoraCommunication lora(868E6, 0xbb, 0xaa);
            Reader reader;
            lora.startLoRa();
            int shift = 0;

            // Perform handshake and connect to the reader
            bool handshake = lora.performHandshake(shift);
            bool readerConnected = reader.EstablishConnection(shift);

            // If everything works, send the data
            if (handshake && readerConnected)
            {
                std::queue<String> sendQueue = reader.loadDataIntoQueue();
                int nbofACK = lora.sendPackets(sendQueue);

                // Update the cursor to remember progress and close session
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

private:
    unsigned long starting_time; // Keeps track of when the timer started
};

#endif // WAITER_HPP
