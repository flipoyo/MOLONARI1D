
#ifndef WAITER_HPP
#define WAITER_HPP


#include <ArduinoLowPower.h>
#include "Low_Power.hpp"
#include "Lora.hpp"


class Waiter {
public :
    Waiter() {}

    // Use before the programm do any action (measures, saving datas, sending datas) to know how long it last
    void startTimer(){
        starting_time = millis();
    }

    // Put the arduino in low power mode for the desired time (in ms after the start of the timer)
    void sleepUntil(unsigned long desired_waiting_time) {
        unsigned long time_to_wait = (millis() - starting_time) + desired_waiting_time;
        MyLowPower.Sleep(time_to_wait);
    }

    // Put the arduino in delay mode for the desired time (in ms after the start of the timer)
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
