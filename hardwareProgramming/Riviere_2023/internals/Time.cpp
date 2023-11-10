// This file will contain all the code to track time using the integrated Real Time Clock (RTC) of the MKR board


// Check that the file has not been imported before
#ifndef TIME
#define TIME


#include <RTCZero.h>



RTCZero internalRtc;



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
void InitialiseRTC(/* Parameters */) {
  internalRtc.begin();
}


// Return the current date (JJ/MM/AAAA)
String GetCurrentDate() {
  // Todo
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

#endif