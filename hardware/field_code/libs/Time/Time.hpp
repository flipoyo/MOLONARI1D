// This file contains all the code to manage time using the MKR board's integrated Real Time Clock (RTC) and an external RTC.

#ifndef MY_TIME
#define MY_TIME

#include <RTCZero.h>
#include <RTClib.h>
#include <vector>

// Declare the RTC objects: internal (MKR) and external
extern RTCZero internalRtc;
extern RTC_PCF8523 externalRtc;
extern std::vector<unsigned long> measurementTimesVec;
extern int measurementCount;

// Helper function to convert an integer to a 2-digit string (e.g., 7 -> "07")
String UIntTo2DigitString(uint8_t x);

// Initialize both the internal and external RTCs
void InitialiseRTC();
void RefreshConfigFromFile();

// Get the current date in "DD/MM/YYYY" format
String GetCurrentDate();

// Get the current time in "HH:MM:SS" format
String GetCurrentHour();

// Get the current time in seconds since midnight
unsigned long GetSecondsSinceMidnight();


// Initialize the array with all the measurement times (in seconds from midnight)
void InitializeMeasurementTimes();

// Determine how many measurements have already been done today
void InitializeMeasurementCount();

// Calculate the time (in ms) until the next measurement
unsigned long CalculateSleepTimeUntilNextMeasurement();

void LoadConfig();

#endif // MY_TIME
