# Timestamping Data and Using Clocks

## Why?

The Arduino board used has an internal RTC that allows access to the time elapsed SINCE the board was powered on, which means it tracks relative time, not absolute time. To obtain the real date and time, we use an external clock that is part of the Adalogger.

## How?

After each power-up, we request the current date from the external clock (`.now()`), which is then used to initialize the internal clock (`.setDate()` and `.setTime()`). The internal clock can then measure elapsed time and timestamp the measurements.  
Be careful not to use `.millis()` as it will overflow over the duration of the mission and, more importantly, it does not account for time spent while the board is in sleep mode.

## What's Next?

The long-term goal is to request the time from the server, thus eliminating the need for the external RTC module. That's why the code does not constantly request the date and time from the external RTC module.

## Useful Links:

External Real-Time Clock: Adafruit Adalogger FeatherWing, RTC_PCF8523  
Documentation link (RTClib): https://adafruit.github.io/RTClib/html/class_r_t_c___p_c_f8523.html  
Connections: https://learn.adafruit.com/adafruit-adalogger-featherwing/pinouts

Internal RTC, the clock within the Arduino MKR WAN 1310  
Documentation link for RTCZero: https://www.arduino.cc/reference/en/libraries/rtczero/  
Note that the documentation is very (very) minimal!
