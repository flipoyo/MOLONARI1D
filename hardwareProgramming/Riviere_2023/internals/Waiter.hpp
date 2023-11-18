// Defines a class to wait in a way that allows each iteration of the main loop to take the same amount of time.

#ifndef WAITER_HPP
#define WAITER_HPP


#include <ArduinoLowPower.h>
#include "Low_Power.hpp"
#include "Lora.hpp"


// A class to wait for a given amount of time after a timer has been started.
// For exemple, you start the timer, do other stuff and then wait until the timer has reached a given amount of time.
class Waiter {
public :
    Waiter() {}

    // Use before the programm do any action (measures, saving datas, sending datas) to know how long it last
    void startTimer(){
        starting_time = millis();
    }

    // Put the arduino in low-power mode for the desired amount of time (in ms after the start of the timer)
    void sleepUntil(unsigned long desired_waiting_time) {
        unsigned long time_to_wait = (millis() - starting_time) + desired_waiting_time;
        MyLowPower.Sleep(time_to_wait);
    }

    // Put the arduino in delay mode for the desired amount of time (in ms after the start of the timer)
    // In this mode, the arduino will still be able to serve the Lora requests
    void delayUntil(unsigned long desired_waiting_time) {
        unsigned long end_date = starting_time + desired_waiting_time;
        while(millis() < end_date) {
            ServeLora();
            delay(1);
        }
    }

private :
    unsigned long starting_time;
};

#endif // WAITER_HPP
