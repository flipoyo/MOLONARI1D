// This file is responsible of switching to low-power mode

#include <ArduinoLowPower.h>

#include "Lora.cpp"


// Switch to low-power mode for a given amount of time
void Sleep(uint32_t millis) {
  SleepLora();

  LowPower.deepSleep(millis);

  WakeUpLora();
}