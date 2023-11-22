// This file will contain all the definitions relative to LoRa communication.
// See internals/Lora.cpp for the implementation.

// Check that the file has not been imported before
#ifndef MY_LORA_H
#define MY_LORA_H

#include <LoRa.h>

#include "Measure.hpp"


// ----- Variables -----

// The id number of the next packet that will be received
unsigned int receivedPacketNumber = 0;
// The id number of the next packet that will be sent
unsigned int sentPacketNumber = 0;

// The nework ID of this device
unsigned int networkId = 42;

float _frequency = 868E6;


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

// Initialise the lora module for the first time. Call before any other LoRa function
void InitialiseLora(float frequency = 868E6);

// Temporarily disable the LoRa module to save battery. It can be waken up with WakeUpLora
void SleepLora();

// Re-enable the LoRa module if it was asleep. I.E. Exit low-power mode for the LoRa module
void WakeUpLora();

void ServeLora();


// ----- Internal functions -----

// Callback function when the lora module receives a packet
// Arguments :
//  packetSize -> Size of the received packet
void OnLoraReceivePacket(int packetSize);

// Respond to an incoming data request
void HandleDataRequest(unsigned int senderId);

// Discards a given amount of data received by LoRa
void ClearBytes(unsigned int length);

// Reads an object in binary from LoRa
template<typename T>
T ReadFromLoRa();

// Sends a data packet through LoRa
// Arguments :
//  payload -> A pointer to the object to send (&obj)
//  payloadSize -> The size of the object to send (sizeof(obj))
//  destinationId -> The address of the destination device of the message
//  requestType -> The type of packet request to send
// Example :
//  SendPacket(&data, sizeof(data), destId, DT_REQ)
bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, RequestType requestType);

// Sends a measurement (DT_RPL) via LoRa
// Arguments :
//  measure -> The measurement to send
//  destinationId -> The address of the destination device of the message 
bool SendMeasurement(Measure measure, unsigned int destinationId);


#include "Lora.cpp"

#endif