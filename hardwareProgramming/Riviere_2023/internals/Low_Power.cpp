// This file is responsible of switching to low-power mode

// Check that the file has not been imported before
#ifndef MY_LOW_MOWER
#define MY_LOW_MOWER


#include <ArduinoLowPower.h>

#include "Lora.cpp"


// Switch to low-power mode for a given amount of time (in milli-seconds)
void Sleep(uint32_t millis) {
  SleepLora();

  LowPower.deepSleep(millis);

  WakeUpLora();
}

#endif