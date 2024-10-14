# The SD card: a bad idea?

This year, we decided to abandon the *data loggers* (i.e., the "data recorders") called "Hobbos" in favor of SD storage (as part of a broader effort to implement data transmission).

To put it simply: for some rather obscure reason, writing to the SD card is **VERY** unpredictable. So, at <u>random</u> moments, the connection with the SD card is lost, and data is not recorded. BUT, there's a problem: we built the code in such a way that data transmission happens from the data stored in memory. So, if we lose data, we also lose the ability to transmit it.

Thus, we will need to solve this rather tricky problem. Don't panic—we still have some potential solutions.

* The first solution involves the Flash memory directly included in the Arduino. Initially, we considered storing the data in the Flash memory of the *MKR WAN 1310* Arduino. It has the advantage of retaining data written to it even when powered off. The issue is that we cannot easily use Flash memory for writing data. So, we have to use a library that allows us to do so. We started looking at the `FlashStorage` library, but it is too "high level," meaning we can only write one piece of data and read one piece of data at a time (so the next data written will overwrite the previous one). However, this library could be used if we apply it at a lower level. Therefore, if you pursue this path, you will need to dig deeper into the workings of the `FlashStorage` library and explore how it can be used at a lower level.

* The second solution is to figure out why this darn SD card is failing (Is the card obsolete? A code issue? A connection problem? A module issue? We tried two: the Adalogger Featherwing and another Arduino-related module, and the same thing happens every time. Is it a problem with the `SD.h` library?). We are fairly confident in the robustness of our code, but it's not a possibility that should be dismissed outright. This is an investigation to carry out if you choose to explore this path. After all, we spent the entire term trying this route without success.

It’s essential to keep in mind that recording is **the most important part of the process**. We need to ensure that every piece of data is recorded because we cannot rely on data transmission alone to offload the data from the card.
