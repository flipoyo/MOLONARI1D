// Check that the file has not been imported before
#ifndef MY_LORA_H
#define MY_LORA_H

#include <LoRa.h>

#include "Measure.hpp"
#include "LoraPacket.hpp"
#include "LoraClient.hpp"


// ----- Variables -----

// The nework ID of this device
unsigned int networkId = 42;

float _frequency = 868E6;

LoraClient clients[CLIENT_COUNT];

// ----- Data type -----

// Represents a type of LoRa request
enum RequestType : uint8_t {
  // Request data (ie measurements)
  DT_REQ = 0x01,
  // Reply data (ie send measurements)
  DT_RPL = 0x81,

  // Request time
  TIME_REQ = 0x02,
  // Reply time
  TIME_RPL = 0x82
};


// ----- Public functions -----

template<uint8_t CLIENT_COUNT>
class LoraDeviceClass {
  public :
    // Constructor
    LoraDeviceClass(unsigned int networkId);

    void Initialise(float frequency = 868E6);
    void Sleep();
    void WakeUp();

    // Sends a data packet through LoRa
    // Arguments :
    //  payload -> A pointer to the object to send (&obj)
    //  payloadSize -> The size of the object to send (sizeof(obj))
    //  destinationId -> The address of the destination device of the message
    //  requestType -> The type of packet request to send
    // Example :
    //  SendPacket(&data, sizeof(data), destId, DT_REQ)
    bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, unsigned int sentPacketNumber, RequestType requestType)
  
  private :
    float frequency;
    const unsigned int networkId;
    bool isActive = false;
    LoraClient clients[CLIENT_COUNT];

    template<uint16_t PAYLOAD_CAPACITY>
    bool TryReadPacket(LoraPacket<PAYLOAD_CAPACITY>& packet, int packetSize);

    bool TryGetClient(LoraClient& client, unsigned int remoteId);

    // Callback function when the lora module receives a packet
    // Arguments :
    //  packetSize -> Size of the received packet
    void OnReceivePacket(int packetSize);
    
    void ClearBytes(unsigned int length);
};

extern LoraDeviceClass<1> LoraDevice;

#include "Lora.cpp"

#endif