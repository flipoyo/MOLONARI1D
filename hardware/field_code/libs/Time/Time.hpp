// This file contains all the code to manage time using the MKR board's integrated Real Time Clock (RTC) and an external RTC.

#ifndef MY_TIME
#define MY_TIME

#include <RTCZero.h>
#include <RTClib.h>

// Declare the RTC objects: internal (MKR) and external
RTCZero internalRtc;
RTC_PCF8523 externalRtc;

// Helper function to convert an integer to a 2-digit string (e.g., 7 -> "07")
String UIntTo2DigitString(uint8_t x);

// Initialize both the internal and external RTCs
void InitialiseRTC();

// Get the current date in "DD/MM/YYYY" format
String GetCurrentDate();

// Get the current time in "HH:MM:SS" format
String GetCurrentHour();

// Get the current time in seconds since midnight
unsigned long GetSecondsSinceMidnight();

// --- Measurement Control ---
// Handles intervals and timing for periodic measurements throughout the day
extern const int MEASURE_INTERVAL_MINUTES; // Interval between measurements
extern const int TOTAL_MEASUREMENTS_PER_DAY; // Total measurements in a day
unsigned int* measurementTimes; // Store times for each measurement
int measurementCount = 0;

// Initialize the array with all the measurement times (in seconds from midnight)
void InitializeMeasurementTimes();

// Determine how many measurements have already been done today
void InitializeMeasurementCount();

// Calculate the time (in ms) until the next measurement
unsigned long CalculateSleepTimeUntilNextMeasurement();

#endif // MY_TIME
