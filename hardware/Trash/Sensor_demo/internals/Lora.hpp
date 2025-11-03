#ifndef LORA_HPP
#define LORA_HPP

#include <Arduino.h>
#include <LoRa.h>
#include <queue>
#include <unordered_set>
enum RequestType : uint8_t {

  SYN = 0xcc,
  ACK = 0x33,
  DATA = 0xc3,
  FIN = 0x3c

};

// MANQUE LA DECLARATION D'UNE CONSTANTE
class LoraCommunication {
public:
    LoraCommunication(long frequency, uint8_t localAdd , uint8_t desti);

    // Method to start (initialize) LoRa
    void startLoRa();

    // Method to stop (deactivate) LoRa
    void stopLoRa();
// IL MANQUE LA FONCTION SETDESTTODEFAULT
    // Send a structured packet
    void sendPacket(const uint8_t packetNumber, const RequestType requestType, const String &payload);

    // Receive and parse a structured packet
    bool receivePacket(uint8_t &packetNumber,RequestType &requestType, String &payload);

    bool isValidDestination(int recipient, int dest, RequestType requestType);

    uint8_t calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload);

    // PAS LA MEME FONCTION APPELEE
    bool performHandshake(int &shift);
    
    //PAS LA MEME FONCTION APPELEE
    uint8_t sendPackets(std::queue<String> &sendQueue);

    // PAS LA MEME NATURE D'OBJET EN ARGUMENT
    void closeSession(uint8_t lastPacket);

    // Method to check if LoRa is active
    bool isLoRaActive();

private:
    long freq;
    uint8_t localAddress;
    uint8_t destination;
    bool active; // Internal flag to track whether LoRa is currently active
    std::unordered_set<uint8_t> myNet = {0xaa}; // PAS LA MEME CHOSE ENTRE ACCOLADE
};
#include "Lora.cpp"
#endif // LORA_HPP
