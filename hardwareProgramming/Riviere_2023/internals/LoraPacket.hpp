#ifndef LORA_PACKET_HPP
#define LORA_PACKET_HPP

#include "Lora.hpp"

template <uint16_t PAYLOAD_CAPACITY>
class LoraPacket
{
public:
    /* data */
    const unsigned int senderId;
    const unsigned int receiverId;

    const unsigned int packetNumber;

    const RequestType requestType;

    const int payloadSize;
    const uint8_t[PAYLOAD_CAPACITY] payload;


    LoraPacket() : senderId(0), receiverId(0), packetNumber(0), requestType(DT_REQ), payloadSize(0), payload() {};
    LoraPacket(unsigned int senderId, unsigned int receiverId, unsigned int packetNumber, RequestType requestType, const uint8_t *payload, int payloadSize);

    template<typename T>
    T Read(uint8_t index) const {
        return *reinterpret_cast<T*>(&payload[index]);
    }
};

#endif // LORA_PACKET_HPP