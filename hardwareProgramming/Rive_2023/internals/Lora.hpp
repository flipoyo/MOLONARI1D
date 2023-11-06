// Check that the file has not been imported before
#ifndef MY_LORA_H
#define MY_LORA_H

#include <LoRa.h>

#include "Measure.h"

// The id number of the next packet that will be received
unsigned int receivedPacketNumber = 0;
// The id number of the next packet that will be sent
unsigned int sentPacketNumber = 0;

// The nework ID of this device
unsigned int networkId = 0;

// Function called when a measure is received
void (*onGetMeasureCallback)(Measure);


enum RequestType : unsigned char {
  DT_REQ = 0x01,
  DT_RPL = 0x81,
  TIME_REQ = 0x02,
  TIME_RPL = 0x82
};


void InitialiseLora(void (*onGetMeasureCallback)(Measure), float frequency = 868E6);
void SleepLora();
void WakeUpLora();

bool RequestMeasurement(unsigned int lastMeasurementId, unsigned int destinationId);

void OnLoraReceivePacket(int packetSize);
void HandleDataReplyPacket();

void ClearBytes(unsigned int length);
template<typename T>
T ReadFromLoRa();

bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, RequestType requestType);


#include "Lora.cpp"

#endif