#include <ArduinoLowPower.h>
#include "Low_Power.hpp"

// use before the programm do any action ( measures, saving datas, sending datas) to know how long it last
// return the time in miliseconds from the internal clock (time_start)
void when_start(){
    return millis()
}

// compute the time all actions have taken to know the real time to wait if we want to have desired_waiting time between each data send
// you do not need to call this function as it is callled in wait_correct_time
void time_difference( unsigned long time_start, unsigned long desired_waiting_time){
    actual_time = millis()
    unsigned long time_difference = actual_time - time_start
    return unsigned long (desired_waiting_time - time_difference) 
}
// call this fonction to go on low power mode for the desired time
// input :
// time_start : time measured before the programm do any action as returned by when_start
// desired_waiting time : time you want to have between two packet send
void wait_correct_time(unsigned long time_start, unsigned long desired_waiting_time){
    unsigned long time_to_wait = time_difference(time_start,desired_waiting_time)
    MyLowPower.Sleep(time_to_wait)
}