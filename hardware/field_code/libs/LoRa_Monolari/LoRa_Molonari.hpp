 #ifndef LORA_HPP
#define LORA_HPP

#include <Arduino.h>
#include <LoRa.h>
#include <queue>
#include <unordered_set>

enum RequestType : uint8_t {
    SYN  = 0xcc,
    ACK  = 0x33,
    DATA = 0xc3,
    FIN  = 0x3c
};

enum RoleType : uint8_t {
    MASTER,
    SLAVE
};

const int MAX_QUEUE_SIZE = 255; // Limite pour les queues

class LoraCommunication {
public:
    LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti, RoleType role);

    void startLoRa();
    void stopLoRa();
    void setdesttodefault();

    // Communication
    void sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload);
    bool receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload);
    bool isValidDestination(int recipient, int dest, RequestType requestType);
    uint8_t calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload);
    bool isLoRaActive();

    // Sessions
    bool handshake(uint8_t &shift);
    uint8_t sendPackets(std::queue<String> &sendQueue);
    int receivePackets(std::queue<String> &receiveQueue);
    bool closeSession(int lastPacket);

    bool receiveConfigUpdate(const char* filepath, uint16_t* outMeasureInterval, uint16_t* outLoraInterval, unsigned long timeout_ms = 15000);
private:
    long freq;
    uint8_t localAddress;
    uint8_t destination;
    bool active;
    RoleType deviceRole;
    std::unordered_set<uint8_t> myNet = {0xaa, 0xbb, 0xcc};
};

#endif


