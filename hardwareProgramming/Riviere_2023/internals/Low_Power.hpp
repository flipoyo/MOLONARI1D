
#ifndef LOW_POWER_HPP
#define LOW_POWER_HPP

class MyLowPowerClass {
public:
    // Switch to low-power mode for a given amount of time (in milli-seconds)
    void Sleep(uint32_t millis);

private :
    // The original pinMode of each pin
    int pinModes[NUM_DIGITAL_PINS];

    // Disable all IO pins to save battery
    void DisableAllIOPins();
    // Re-enable all IO pins, and sets them to their original mode
    void EnableAllIOPins();
    // Get the pinMode of a given pin
    int GetPinMode(uint8_t pin);
};

extern MyLowPowerClass MyLowPower;

#include "Low_Power.cpp"

#endif // LOW_POWER_HPP
