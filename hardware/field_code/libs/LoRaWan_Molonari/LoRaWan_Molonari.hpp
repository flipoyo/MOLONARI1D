#ifndef LORAWAN_HPP
#define LORAWAN_HPP

#include <Arduino.h>
#include <MKRWAN.h>
#include <queue>
#include <SD.h>

class LoraWANCommunication {
public:
    LoraWANCommunication();
    bool begin(const String& appEui, const String& appKey);
    bool sendQueue(std::queue<String>& sendingQueue);
    bool receiveConfig(const char* configFilePath, bool modif);

private:
    LoRaModem modem;
};

#endif



