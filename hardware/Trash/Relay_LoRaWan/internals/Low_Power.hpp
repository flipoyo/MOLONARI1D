// This file is responsible of switching to low-power mode
// See internals/Low_Power.cpp for the implementation.

// Check that the file has not been imported before
#ifndef LOW_POWER_HPP
#define LOW_POWER_HPP

// The code is inside a class to tidy up which functions corresponds to which functionnality

class MyLowPowerClass {
public:
    // Switch to low-power mode for a given amount of time (in milli-seconds)
    void Sleep(uint32_t millis);

private :
    // The original pinMode of each pin
    // This functionnality is deprecated as tests show that disabling pins does not save up battery
    int pinModes[NUM_DIGITAL_PINS];

    // Disable all IO pins to save battery
    // This functionnality is deprecated as tests show that disabling pins does not save up battery
    void DisableAllIOPins();
    // Re-enable all IO pins, and sets them to their original mode
    // This functionnality is deprecated as tests show that disabling pins does not save up battery
    void EnableAllIOPins();
    // Get the pinMode of a given pin
    // This functionnality is deprecated as tests show that disabling pins does not save up battery
    int GetPinMode(uint8_t pin);
};

// Create an instance of the class, so that the functions are accessible from outside the file

// A collection of methods to put the Arduino into low-power mode.
extern MyLowPowerClass MyLowPower;

#include "Low_Power.cpp"

#endif // LOW_POWER_HPP
