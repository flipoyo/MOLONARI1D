#ifndef LORAWAN_HPP
#define LORAWAN_HPP

#include <Arduino.h>
#include <MKRWAN.h>
#include <queue>

class LoraWANCommunication {
public:
    LoraWANCommunication();
    bool begin(const String& appEui, const String& appKey);
    bool sendQueue(std::queue<String>& sendingQueue);

private:
    LoRaModem modem;
};

#endif



