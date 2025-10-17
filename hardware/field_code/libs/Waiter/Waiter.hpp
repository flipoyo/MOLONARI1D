#ifndef WAITER_HPP
#define WAITER_HPP

#include <queue>
#include <Arduino.h>
#include "Low_Power.hpp" 
#include "Reader.hpp"
#include "LoRa_Molonari.hpp"

class Waiter
{
public:
    // Default constructor, no setup needed here
    Waiter();

    void startTimer();

    void sleepUntil(unsigned long desired_waiting_time);
    
    void delayUntil(unsigned long desired_waiting_time, RoleType role);

private:
    unsigned long starting_time;
};

#endif