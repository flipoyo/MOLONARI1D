// This file will contain all the code to track time using the integrated Real Time Clock (RTC) of the MKR board and the external one.


// Check that the file has not been imported before
#ifndef MY_TIME
#define MY_TIME


#include <RTCZero.h>
#include <RTClib.h>



RTCZero internalRtc;
RTC_PCF8523 externalRtc;


String UIntTo2DigitString(uint8_t x) {
  String str = String(x);

  if (x < 10) {
    str = "0" + str;
  }

  if (x >= 100) {
    str.remove(2);
  }

  return str;
}


// Initialise the RTC module for the first time.
void InitialiseRTC() {
  // Start the internal RTC
  internalRtc.begin();
  
  // Start communication with the external RTC
  bool success = externalRtc.begin();
  if (!success) {
    return;
  }
  
  // If the external RTC has lost power (even its battery), then set its time to the date at which the code was compiled.
  if (externalRtc.lostPower()) {
    externalRtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
  
  // Set the time of the internal RTC to the time of the external one
  DateTime startingDate = externalRtc.now();
  uint8_t day = startingDate.day();
  uint8_t month = startingDate.month();
  uint8_t year = startingDate.year() % 100;
  uint8_t hour = startingDate.hour();
  uint8_t minute = startingDate.minute();
  uint8_t second = startingDate.second();
  internalRtc.setDate(day, month, year);
  internalRtc.setTime(hour, minute, second);
}

// Return the current date (JJ/MM/AAAA)
String GetCurrentDate() {
  return 
    UIntTo2DigitString(internalRtc.getDay()) +
    "/" +
    UIntTo2DigitString(internalRtc.getMonth()) +
    "/" +
    "20" + UIntTo2DigitString(internalRtc.getYear());
}

// Return the current hour (HH:MM:SS)
String GetCurrentHour() {
  return 
    UIntTo2DigitString(internalRtc.getHours()) +
    ":" +
    UIntTo2DigitString(internalRtc.getMinutes()) +
    ":" +
    UIntTo2DigitString(internalRtc.getSeconds());  

}


// Function to get the current time in minutes since midnight
unsigned long GetSecondsSinceMidnight() {
    uint8_t hour = internalRtc.getHours();
    uint8_t minute = internalRtc.getMinutes();
    uint8_t second = internalRtc.getSeconds();
    return hour * 3600 + minute * 60 + second; // Return the current time in seconds since midnight
}


// --- Measurement Control ---
// Manage the timing and intervals of measurements taken throughout the day
const int MEASURE_INTERVAL_MINUTES = 3 ; // Measurement interval in minutes
const int TOTAL_MEASUREMENTS_PER_DAY = 1440/MEASURE_INTERVAL_MINUTES ; // 96 measurements in a day
unsigned int measurementTimes[TOTAL_MEASUREMENTS_PER_DAY]; // Array to store measurement times
int measurementCount = 0; // Counter for measurements
int NbMeasurements = 1; // Number of measurements taken

// Function to initialize the measurement time intervals
void InitializeMeasurementTimes() {
  for (int i = 0; i < TOTAL_MEASUREMENTS_PER_DAY; i++) {
    measurementTimes[i] = i * MEASURE_INTERVAL_MINUTES * 60; // Store times in seconds from midnight
  }
}

// Function to initialize the measurement count
void InitializeMeasurementCount() {
  // Get current time from the RTC in minutes since midnight (00:00)
  unsigned long currentTime = GetSecondsSinceMidnight();
  measurementCount = 0; // Counter for measurements
  NbMeasurements = 1; // Number of measurements taken
  for (int i = 0; i < TOTAL_MEASUREMENTS_PER_DAY; i++) {
    if (currentTime > measurementTimes[i]) {
      measurementCount++;
      NbMeasurements++;
    }
    else {
      break; // If the current time is less than the next measurement time, break the loop
    }
  }
}

// Function to calculate the sleep time until the next measurement time
unsigned long CalculateSleepTimeUntilNextMeasurement() {
  // Get current time from the RTC in minutes since midnight (00:00)
  unsigned long currentTime = GetSecondsSinceMidnight();

  // Test code
  // Serial.println("Current time: " + String(currentTime));

  // Find the next measurement time
  for (int i = 0; i < TOTAL_MEASUREMENTS_PER_DAY; i++) {
    if (currentTime < measurementTimes[i]) {
      unsigned long nextTime = measurementTimes[i];
      // Calculate the time difference in milliseconds
      unsigned long sleepTime = (nextTime - currentTime) * 1000; // Convert minutes to milliseconds
      return sleepTime;
    }
  }
  // If no upcoming time found (current time is beyond the last time slot), calculate time until the next day's first measurement
  unsigned long nextDayFirstTime = measurementTimes[0] + 24 * 3600; // Add 24 hours to the first time slot (start of the next day)
  unsigned long sleepTime = (nextDayFirstTime - currentTime) * 1000;
  return sleepTime;
}

#endif