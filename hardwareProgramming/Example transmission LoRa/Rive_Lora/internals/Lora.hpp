#ifndef LORA_HPP
#define LORA_HPP

#include <Arduino.h>
#include <LoRa.h>
#include <queue>
#include <unordered_set>

enum RequestType : uint8_t {

  SYN = 0x01,
  ACK = 0x51,
  DATA = 0x10,
  FIN = 0x92

};
const int MAX_QUEUE_SIZE = 255;  // Queue size limit for the receiver
class LoraCommunication {
public:
    LoraCommunication(long frequency, uint8_t localAdd , uint8_t desti);

    // Method to start (initialize) LoRa
    void startLoRa();

    // Method to stop (deactivate) LoRa
    void stopLoRa();

    // Send a structured packet
    void sendPacket(const uint8_t packetNumber, const RequestType requestType, const String &payload);

    // Receive and parse a structured packet
    bool receivePacket(uint8_t &packetNumber,RequestType &requestType, String &payload);

    bool isValidDestination(int recipient, int dest, RequestType requestType);

    uint8_t calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload);

    bool performHandshake( uint8_t shiftback);
    
    int receivePackets(std::queue<String> &receiveQueue);

    void closeSession(int lastPacket);

    // Method to check if LoRa is active
    bool isLoRaActive();

private:
    long freq;
    uint8_t localAddress;
    uint8_t destination;
    bool active; // Internal flag to track whether LoRa is currently active
    std::unordered_set<uint8_t> myNet = {0xbb , 0xcc};
};
#include "Lora.cpp"
#endif // LORA_HPP
