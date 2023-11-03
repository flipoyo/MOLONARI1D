// Check that the file has not been imported before
#ifndef MY_LORA_H
#define MY_LORA_H

#include <LoRa.h>

#include "Internal_Log.cpp"
#include "Measure.h"

// The id number of the next packet that will be received
unsigned int receivedPacketNumber = 0;
// The id number of the next packet that will be sent
unsigned int sentPacketNumber = 0;

// The nework ID of this device
unsigned int networkId = 42;


enum RequestType : char {
  DT_REQ = 0x01,
  DT_RPL = 0x81,
  TIME_REQ = 0x02,
  TIME_RPL = 0x82
};


void InitialiseLora(float frequency = 868E6);
void SleepLora();
void WakeUpLora();

void OnLoraReceivePacket(int packetSize);
void HandleDataRequest(unsigned int senderId);

void ClearBytes(unsigned int length);
template<typename T>
T ReadFromLoRa();

bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, RequestType requestType);
bool SendMeasurement(Measure measures, unsigned int destinationId);


#include "Lora.cpp"

#endif