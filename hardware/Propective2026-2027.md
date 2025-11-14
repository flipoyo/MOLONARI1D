For the attention of 2A mineurs in 2026/2027

THE GOLDEN COMMIT WORKS GET BACK TO IT IF ISSUES (THE DEMO CODES).

1. This year’s final version

Some things work:
We use Arduino MKR WAN 1310 boards.
PlatformIO works well and allows handling of both external and internal project libraries. The management of the platformio.ini file depends on how the project evolves, but it can probably be kept largely as is.
Everything is neatly organized; the structure is clear: libraries on one side and the main files for each board on the other.
Everything compiles correctly on the computer, and uploading to the boards works.
We are able to receive information from the board: SD initialization, configuration reading, measurement launching, and local storage.
We are able to make the relay board and the sensor board communicate: BE CAREFUL to always update the config files stored on the SD cards with the correct values (for example, the devEui and appEui for inter-board communication).
We are able to send data from the relay to the gateway, from the gateway to the server, and from the server to the website.

2. Next steps

There are several things planned for implementation that were designed this year:
Implement support for multiple sensor boards connected to the same relay. The relay must be able to receive information from different boards, each with its own ID, and handle the data arrival times properly.
There is a problem because the current gateway cannot send downlink data; it can only receive. It will need to be replaced by a Raspberry Pi. You will need to code its LoRaWAN data reception and internet forwarding. With that, you must also add the handling of downlink data at both the relay and the sensor: receiving the config file and replacing the one stored on the SD card. It may seem like a lot of work for a small outcome, and many issues can arise: corrupted files making measurements impossible on the relay or sensor, desynchronization if only one device updates the file, loss of subsequent data, etc.
Optimize the libraries to make them clearer: small libraries containing only basic functions and not calling each other; larger grouped libraries that call the smaller ones to form the main building blocks, which are then used in the main files.
As you will see in the paragraph below, the time management is not satisfactory at all. To avoid communication window shifts, you must:
Add a function that computes all communication times of the day based on the requested communication interval.
Modify the code so that communications occur at fixed times rather than after a time interval.
RTC clocks can drift up to 2 seconds per day and up to 5 minutes per month. Therefore, implement a function that updates both boards’ clocks weekly using the internet time via the gateway, to limit drift and maintain communication.
(NOTE: You do not need to modify this for measurements, since the boards don’t need to be synchronized for that—this already works very well.
VERY IMPORTANT NOTE: Once the files are uploaded, do not press reset again, as it shifts the clocks.)

3. Anything else?
A few general notes:
It’s helpful to know how to code in C++; otherwise check basic tutorials online.
Understanding the project structure and the code takes time—good luck.
We hope everything will work!
Uploading to the boards is a real hassle on a Mac—do it on Windows.
When uploading the program to the boards, you must press the reset button twice when the message “Waiting for the new upload port...” appears; this reinitializes the board.
To check if the boards are functioning properly, they should blink regularly with an orange light.
About the clocks: the RTC clock is set to the time of the last COMPILATION, so once the code is uploaded, pressing reset sets it back to the compilation time → this can cause several hours of offset! At the beginning, do NOT press reset after uploading, and compile all codes at the same time.