#ifndef LORA_HPP
#define LORA_HPP

#include <Arduino.h>
#include <LoRa.h>
enum RequestType : uint8_t {
 
  SYN = 0x01,
  ACK = 0x51,
  DATA = 0x10,
  FIN = 0x92
};
class LoraCommunication {
public:
    LoraCommunication(long frequency, uint8_t localAddress);

    // Method to start (initialize) LoRa and set control flag
    void startLoRa();

    // Method to stop (deactivate) LoRa and reset control flag
    void stopLoRa();

    // Send a structured packet
    void sendPacket(const uint8_t &destination,const uint8_t packetNumber, const RequestType requestType, const String &payload);

    // Receive and parse a structured packet
    bool receivePacket(uint8_t &sender, uint8_t &packetNumber,RequestType &requestType, String &payload);

    // Method to check if LoRa is active
    bool isLoRaActive();

private:
    long freq;
    uint8_t localAddress;
    bool active; // Internal flag to track whether LoRa is currently active
};
#include "Lora.cpp"
#endif // LORA_HPP
