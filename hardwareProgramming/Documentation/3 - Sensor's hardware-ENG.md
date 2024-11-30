# The sensor's hardware

## The SD card: a bad idea?

Updated by MOLONARI2024 team

As part of a broader effort to implement data transmission, we transitioned from using *data loggers* (e.g., "Hobbos") to SD card storage.

To put it simply: for some rather obscure reason, writing to the SD card is **SOMETIMES** unpredictable. So, at <u>random</u> moments, the connection with the SD card is lost, and data is not recorded. BUT, there's a problem: we built the code in such a way that data transmission happens from the data stored in memory. So, if we lose data, we also lose the ability to transmit it.

This year, the problem has been mitigated, likely due to improvements in our code and changes in the way data is read, including the implementation of the Queue library. Additionally, adjustments to the breadboard connections appear to have helped reduce these issues. Nevertheless, the root cause remains unknown. To fully address this challenge, we propose the following potential solutions:

### 1. Explore Flash Memory Storage
The MKR WAN 1310 Arduino includes onboard *Flash memory* capable of retaining data even when powered off. This could provide a more reliable storage option. However, writing to Flash memory is not straightforward. We started looking at the `FlashStorage` library, but it is too "high level," meaning we can only write one piece of data and read one piece of data at a time (so the next data written will overwrite the previous one). However, this library could be used if we apply it at a lower level. Therefore, if you choose this path, further research and development will be necessary.if you pursue this path, you will need to dig deeper into the workings of the `FlashStorage` library and explore how it can be used at a lower level.

### 2. Investigate SD Card Issues
Understanding why the SD card fails remains crucial. Possible causes include:
* Card obsolescence
* Code-related issues
* Connection instability
* Module incompatibility
* Bugs in the SD.h library

We tested two modules—the Adalogger Featherwing and another Arduino-compatible module—but experienced the same issues with both. While recent code enhancements and hardware adjustments reduced the problem's frequency, the underlying cause remains elusive. A detailed investigation into these aspects is essential.

It’s essential to keep in mind that recording is **the most important part of the process**. We need to ensure that every piece of data is recorded because we cannot rely on data transmission alone to offload the data from the card. Even if this problem arrives once in a while it is importand to understand why.

# Progress

To ensure data transmission between the relay and the sensor this year we implemented a new way of reading data from the SD card: the use of the `Queue` library. This library allows working with data queues in embedded systems and will hold our data during the communication with the relay through a queue in which the elements are stored and processed in the order in which they are added, following the FIFO (First In, First Out) methodology. This queue is stored or retained in the Arduino's RAM and is cleared each time confirmation is received that the relay has all the data. 

Evitar entrar al SD card para sacar cada medicion


## Timestamping Data and Using Clocks

Work of MOLONARI2023 team, not updated yet by MOLONARI2024 team

### Why?

The Arduino board used has an internal RTC that allows access to the time elapsed SINCE the board was powered on, which means it tracks relative time, not absolute time. To obtain the real date and time, we use an external clock that is part of the Adalogger.

### How?

After each power-up, we request the current date from the external clock (`.now()`), which is then used to initialize the internal clock (`.setDate()` and `.setTime()`). The internal clock can then measure elapsed time and timestamp the measurements.  
Be careful not to use `.millis()` as it will overflow over the duration of the mission and, more importantly, it does not account for time spent while the board is in sleep mode.

### What's Next?

The long-term goal is to request the time from the server, thus eliminating the need for the external RTC module. That's why the code does not constantly request the date and time from the external RTC module.

### Useful Links:

External Real-Time Clock: Adafruit Adalogger FeatherWing, RTC_PCF8523  
Documentation link (RTClib): https://adafruit.github.io/RTClib/html/class_r_t_c___p_c_f8523.html  
Connections: https://learn.adafruit.com/adafruit-adalogger-featherwing/pinouts

Internal RTC, the clock within the Arduino MKR WAN 1310  
Documentation link for RTCZero: https://www.arduino.cc/reference/en/libraries/rtczero/  
Note that the documentation is very (very) minimal!
