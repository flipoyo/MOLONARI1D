#include <RTCZero.h>
#include <RTClib.h>

RTCZero internalRtc;
RTC_PCF8523 externalRtc;

// Function to convert a single digit to a two-digit string
String UIntTo2DigitString(uint8_t x) {
    String str = String(x);
    if (x < 10) {
        str = "0" + str; 
    }
    return str;
}

// Function to adjust RTC
void AdjustRTC(int secondsOffset) {
    DateTime now = externalRtc.now();
    DateTime adjustedTime = now + TimeSpan(secondsOffset);
    externalRtc.adjust(adjustedTime);
}

void setup() {
    Serial.begin(9600);
    
    // Initialize RTC
    internalRtc.begin();
    if (!externalRtc.begin()) {
        Serial.println("Can't find RTC!");
        while (1); // Stop the program
    }

    // Adjust RTC in seconds
    AdjustRTC(0);
}

void loop() {
    // Example: Print the current time every second
    DateTime now = externalRtc.now();
    
    // Format the output using the helper function
    String timeString = UIntTo2DigitString(now.hour()) + ":" +
                        UIntTo2DigitString(now.minute()) + ":" +
                        UIntTo2DigitString(now.second());
    
    Serial.println(timeString);
    
    delay(5000); // Wait for 5 seconds
}