#ifndef WAITER_HPP
#define WAITER_HPP

//  #include <cstdint>


class Waiter
{
public:
    // Default constructor, no setup needed here
    Waiter();

    void sleepUntil(long desired_waiting_time);
    
private:
    uint32_t starting_time;
};

#endif