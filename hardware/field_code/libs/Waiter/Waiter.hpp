#ifndef WAITER_HPP
#define WAITER_HPP

#include <cstdint>

// Keep this header lightweight: platform-specific headers (Arduino.h) and
// project-specific headers are moved to the implementation file to avoid
// include-path problems in IDEs/linters.

// Forward-compatible simple API: use standard-width integers and a plain
// integer for the role parameter to avoid depending on RoleType here.
class Waiter
{
public:
    // Default constructor, no setup needed here
    Waiter();

    void sleepUntil(long desired_waiting_time);
    
    void delayUntil(uint32_t desired_waiting_time, int role);

private:
    uint32_t starting_time;
};

#endif