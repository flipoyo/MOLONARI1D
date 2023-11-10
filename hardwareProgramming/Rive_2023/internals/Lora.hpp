// This file will contain all functions relative to LoRa communication

// Check that the file has not been imported before
#ifndef MY_LORA_H
#define MY_LORA_H

#include <LoRa.h>

#include "Measure.h"


// ----- Variables -----

// The id number of the next packet that will be received
unsigned int receivedPacketNumber = 0;
// The id number of the next packet that will be sent
unsigned int sentPacketNumber = 0;

// The nework ID of this device
unsigned int networkId = 0;

// Function called when a measure is received
void (*onGetMeasureCallback)(Measure);


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
// Arguments :
//  onGetMeasureCallback -> Fonction qui prend en argument une mesure et qui ne renvoit rien. Elle sera appelée quand une mesure est reçue.
//  frequency -> Fréquence de la porteuse en Hz
void InitialiseLora(void (*onGetMeasureCallback)(Measure), float frequency = 868E6);

// Temporarily disable the LoRa module to save battery. It can be waken up with WakeUpLora
void SleepLora();

// Re-enable the LoRa module if it was asleep. I.E. Exit low-power mode for the LoRa module
void WakeUpLora();

// Send a DT_REQ request on LoRa
// Arguments :
//  firstMissingId -> Id number of the first measure that this card does not know
//  destinationId -> Address of the sensor that we want to request data from
bool RequestMeasurement(uint32_t firstMissingId, unsigned int destinationId);



// ----- Internal functions -----

// Callback function when the lora module receives a packet
// Arguments :
//  packetSize -> Size of the received packet
void OnLoraReceivePacket(int packetSize);

// Read an incoming data reply request
void HandleDataReplyPacket();

// Discards a given amount of data received by LoRa
void ClearBytes(unsigned int length);

// Reads an object in binary from LoRa
template<typename T>
T ReadFromLoRa();

// Sends a data packet through LoRa
//
// Arguments :
//  payload -> A pointer to the object to send (ex : &obj)
//  payloadSize -> The size of the object to send (ex : sizeof(obj))
//  destinationId -> The address of the destination device of the message
//  requestType -> The type of packet request to send
//
// Example :
//  SendPacket(&data, sizeof(data), destId, DT_REQ)
bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, RequestType requestType);


#include "Lora.cpp"

#endif