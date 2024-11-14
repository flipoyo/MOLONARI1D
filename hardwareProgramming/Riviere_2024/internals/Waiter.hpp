// Defines a class to manage waiting in a way that allows each iteration of the main loop to take the same amount of time.
// This file provides an implementation of timed waiting that supports low-power mode for efficient power use.

// Check that the file has not been imported before
#ifndef WAITER_HPP
#define WAITER_HPP

#include <ArduinoLowPower.h>
#include "Reader.hpp"
#include "Low_Power.hpp"
#include "Lora.hpp"
#include <queue>

// A class to wait for a given amount of time after a timer has been started.
// For example, you start the timer, do other stuff and then wait until the timer has reached a given amount of time.
class Waiter
{
public:
// Default constructor
    Waiter() {}

//Use this at the start to record the current time. This way, we can check later how long other tasks (like measurements or data saving) actually take.
    {
        starting_time = millis();
    }

    // Puts the arduino in low-power mode for the desired amount of time (in ms after the start of the timer)
    void sleepUntil(unsigned long desired_waiting_time)
    {
        unsigned long time_to_wait = (starting_time - millis()) + desired_waiting_time;

        // For testing: Print how long we’ll be asleep in milliseconds
        Serial.println("Sleeping for " + String(time_to_wait) + " ms");
        MyLowPower.Sleep(time_to_wait); // Go to low-power mode for the calculated time
    }

    // Put the arduino in delay mode for the desired amount of time (in ms after the start of the timer)
    // In this mode, the arduino will still be able to serve the Lora requests
    void delayUntil(unsigned long desired_waiting_time)
    {
        unsigned long end_date = starting_time + desired_waiting_time;
        
        // Loop until time’s up, handling communication while we wait
        while (millis() < end_date)
        {
            Serial.println("Starting new communication session...");
            // Set up LoRa for communication
            LoraCommunication lora(868E6, 0xbb, 0xaa);
            Reader reader;
            lora.startLoRa();
            int shift = 0;

             // Do handshake and connect to reader
            bool handshake = lora.performHandshake(shift);
            bool readerConnected =  reader.EstablishConnection(shift);

             // If all goes well, send the data
            if ( handshake && readerConnected)
            {
                std::queue<String> sendQueue = reader.loadDataIntoQueue();  // Get the data ready to send
                int nbofACK = lora.sendPackets(sendQueue); // Send it and count acknowledgments
                lora.closeSession(nbofACK); // End LoRa session
                reader.UpdateCursor(nbofACK); // Move the reader's cursor forward based on the data sent
                

            }

            lora.stopLoRa(); // End LoRa communication
            reader.Dispose(); // Clean up the reader

            delay(1); // Tiny delay to avoid endless looping
        }
    }

private:
    unsigned long starting_time; // Keeps track of when we started the wait
};

#endif // WAITER_HPP
