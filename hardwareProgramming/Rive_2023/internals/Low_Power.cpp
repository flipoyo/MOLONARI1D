// This file is responsible of switching to low-power mode

// Check that the file has not been imported before
#ifndef MY_LOW_POWER
#define MY_LOW_POWER


#include <ArduinoLowPower.h>

#include "Lora.hpp"


// Switch to low-power mode for a given amount of time (in milli-seconds)
void MyLowPowerClass::Sleep(uint32_t millis) {
  // Disable all power-consuming features
  SleepLora();
  DisableAllIOPins();

  // Wait
  LowPower.deepSleep(millis);

  // Enable back all the features that werer disabled.
  EnableAllIOPins();
  WakeUpLora();
}


// Disable all IO pins to save battery
void MyLowPowerClass::DisableAllIOPins() {
  for (uint8_t pin = 0; pin < NUM_DIGITAL_PINS; pin++)
  {
    // Skip the reset pin as it has to remain an output low.
    if (pin == LORA_RESET) continue;

    // Save the pin mode to restore it later
    pinModes[pin] = GetPinMode(pin);
    // Set the pin to input pullup to save battery
    pinMode(pin, INPUT_PULLUP);
  }
}


// Re-enable all IO pins, and sets them to their original mode
void MyLowPowerClass::EnableAllIOPins() {
  for (uint8_t pin = 0; pin < NUM_DIGITAL_PINS; pin++)
  {
    pinMode(pin, pinModes[pin]);
  }

  // TODO : Is the original output still the same ?
}


// Get the pinMode of a given pin
int MyLowPowerClass::GetPinMode(uint8_t pin)
{
  // Check that the pin is valid
  if (pin >= NUM_DIGITAL_PINS) return (-1);

  // Get if it is an input or an output
  uint32_t bit = digitalPinToBitMask(pin);
  PortGroup* port = digitalPinToPort(pin);
  volatile uint32_t *reg = portModeRegister(port);
  if (*reg & bit) return (OUTPUT);

  // Get if it is a pullup or not
  volatile uint32_t *out = portOutputRegister(port);
  return ((*out & bit) ? INPUT_PULLUP : INPUT);
}

#endif