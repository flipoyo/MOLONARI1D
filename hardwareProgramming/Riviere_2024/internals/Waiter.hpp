// Defines a class to wait in a way that allows each iteration of the main loop to take the same amount of time.

// Check that the file has not been imported before
#ifndef WAITER_HPP
#define WAITER_HPP

#include <ArduinoLowPower.h>
#include "Reader.hpp"
#include "Low_Power.hpp"
#include "Lora.hpp"
#include <queue>

// A class to wait for a given amount of time after a timer has been started.
// For exemple, you start the timer, do other stuff and then wait until the timer has reached a given amount of time.
class Waiter
{
public:
    Waiter() {}

    // Use before the programm do any action (measures, saving datas, sending datas) to know how long it last
    void startTimer()
    {
        starting_time = millis();
    }

    // Put the arduino in low-power mode for the desired amount of time (in ms after the start of the timer)
    void sleepUntil(unsigned long desired_waiting_time)
    {
        unsigned long time_to_wait = (starting_time - millis()) + desired_waiting_time;

        // Test code
        Serial.println("Sleeping for " + String(time_to_wait) + " ms");
        MyLowPower.Sleep(time_to_wait);
    }

    // Put the arduino in delay mode for the desired amount of time (in ms after the start of the timer)
    // In this mode, the arduino will still be able to serve the Lora requests
    void delayUntil(unsigned long desired_waiting_time)
    {
        unsigned long end_date = starting_time + desired_waiting_time;
        while (millis() < end_date)
        {
            Serial.println("Starting new communication session...");
            LoraCommunication lora(868E6, 0xbb, 0xaa);
            Reader reader;
            lora.startLoRa();
            int shift = 0;
            bool handshake = lora.performHandshake(shift);
            bool readerConnected =  reader.EstablishConnection(shift);
            if ( handshake && readerConnected)
            {
                std::queue<String> sendQueue = reader.loadDataIntoQueue();
                int nbofACK = lora.sendPackets(sendQueue);
                lora.closeSession(nbofACK);
                reader.UpdateCursor(nbofACK);
                

            }

            lora.stopLoRa();
            reader.Dispose();

            delay(1);
        }
    }

private:
    unsigned long starting_time;
};

#endif // WAITER_HPP
