#ifndef LORA_HPP
#define LORA_HPP

#include <Arduino.h>
#include <LoRa.h>
#include <queue>
#include <unordered_set>

// Enum for defining request types in LoRa communication
enum RequestType : uint8_t {
    SYN = 0xcc,  // Synchronization request
    ACK = 0x33,  // Acknowledgment response
    DATA = 0xc3, // Data transmission
    FIN = 0x3c   // End of transmission
};

class LoraCommunication {
public:
    /**
     * Constructor for LoraCommunication.
     * @param frequency The operating frequency of the LoRa module.
     * @param localAdd The local address of this LoRa module.
     * @param desti The destination address for communication.
     */
    LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti);

    // Method to initialize and activate LoRa communication
    void startLoRa();

    // Method to deactivate LoRa communication
    void stopLoRa();

    /**
     * Send a structured packet.
     * @param packetNumber The sequence number of the packet.
     * @param requestType The type of the request (SYN, ACK, DATA, FIN).
     * @param payload The payload data to send.
     */
    void sendPacket(const uint8_t packetNumber, const RequestType requestType, const String &payload);

    /**
     * Receive and parse a structured packet.
     * @param packetNumber Output parameter for the received packet's number.
     * @param requestType Output parameter for the received packet's type.
     * @param payload Output parameter for the received payload.
     * @return True if a packet was successfully received, false otherwise.
     */
    bool receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload);

    /**
     * Validate if the recipient address matches the expected destination.
     * @param recipient The recipient address in the received packet.
     * @param dest The intended destination address.
     * @param requestType The type of the request.
     * @return True if the recipient is valid, false otherwise.
     */
    bool isValidDestination(int recipient, int dest, RequestType requestType);

    /**
     * Calculate a checksum for data integrity validation.
     * @param recipient The recipient address.
     * @param dest The destination address.
     * @param packetNumber The sequence number of the packet.
     * @param requestType The type of the request.
     * @param payload The payload data.
     * @return The calculated checksum as a byte.
     */
    uint8_t calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload);

    /**
     * Perform a handshake process to synchronize with the receiver.
     * @param shift Output parameter to adjust synchronization.
     * @return True if the handshake was successful, false otherwise.
     */
    bool performHandshake(int &shift);

    /**
     * Send a series of packets from a queue.
     * @param sendQueue The queue containing data to send.
     * @return The number of packets successfully sent.
     */
    uint8_t sendPackets(std::queue<String> &sendQueue);

    /**
     * Close the current session after transmission.
     * @param lastPacket The sequence number of the last packet sent.
     */
    void closeSession(uint8_t lastPacket);

    // Check if LoRa communication is currently active
    bool isLoRaActive();

private:
    long freq; // Operating frequency of the LoRa module
    uint8_t localAddress; // Local address of this LoRa module
    uint8_t destination; // Destination address for communication
    bool active; // Internal flag to track whether LoRa is currently active
    std::unordered_set<uint8_t> myNet = {0xaa}; // Set of valid network identifiers
};

#include "Lora.cpp"
#endif // LORA_HPP

