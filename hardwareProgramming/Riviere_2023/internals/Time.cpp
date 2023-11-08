// This file will contain all the code to track time using the integrated Real Time Clock (RTC) of the MKR board


// Check that the file has not been imported before
#ifndef TIME
#define TIME


#include <RTCZero.h>



RTCZero internalRtc;


// Initialise the RTC module for the first time.
void InitialiseRTC(/* Parameters */) {
}


// Return the current date (JJ/MM/AAAA)
String GetCurrentDate() {
  // Todo
  return "01/01/2000";
}

// Return the current hour (HH:MM:SS)
String GetCurrentHour() {
  // Todo
  return "00:00:00";
}

#endif