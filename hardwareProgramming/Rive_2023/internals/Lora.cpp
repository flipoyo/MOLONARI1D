// This file will contain all the functions relative to LoRa communication
// See internals/Lora.hpp for the definitions.

// Check that the file has not been imported before
#ifndef MY_LORA
#define MY_LORA


#include "Lora.hpp"


// Debug methods to enable or disable logging
#ifdef LORA_DEBUG
#define LORA_LOG(msg) Serial.print(msg);
#define LORA_LOG_HEX(msg) Serial.print(msg, HEX);
#define LORA_LOG_LN(msg) Serial.println(msg);
#else
#define LORA_LOG(msg)
#define LORA_LOG_HEX(msg)
#define LORA_LOG_LN(msg)
#endif



// ----- Public functions -----

// Initialise the lora module for the first time. Call before any other LoRa function
void InitialiseLora(void (*_onGetMeasureCallback)(Measure), float frequency) {
  onGetMeasureCallback = _onGetMeasureCallback;

  LoRa.begin(frequency);
  
  LoRa.enableCrc();
  sentPacketNumber = LoRa.random();

  //LoRa.onReceive(OnLoraReceivePacket);
  LoRa.receive();
}


// Temporarily disable the LoRa module to save battery. It can be waken up with WakeUpLora
void SleepLora() {
  LoRa.sleep();
}


// Re-enable the LoRa module if it was asleep. I.E. Exit low-power mode for the LoRa module
void WakeUpLora() {
  // TODO : test that this works
  LoRa.receive();
}


// Send a DT_REQ request on LoRa
// Arguments :
//  firstMissingId -> Id number of the first measure that this card does not know
//  destinationId -> Address of the sensor that we want to request data from
bool RequestMeasurement(uint32_t lastMeasurementId, unsigned int destinationId) {
  return SendPacket(&lastMeasurementId, sizeof(lastMeasurementId), destinationId, DT_REQ);
}


void ServeLora() {
  int packetSize = LoRa.parsePacket();
  if (packetSize != 0) {
    OnLoraReceivePacket(packetSize);
  }
}



// ----- Internal functions -----

// Callback function when the lora module receives a packet
// Arguments :
//  packetSize -> Size of the received packet
void OnLoraReceivePacket(int packetSize) {
  LORA_LOG_LN("Receiving packet");

  // If the header is incomplete, ignore the packet
  if (packetSize < 13) {
    LORA_LOG_LN("Ignoring packet : wrong size");
    ClearBytes(packetSize);
    return;
  }

  // Get sender and destination
  unsigned int senderId = ReadFromLoRa<unsigned int>();
  unsigned int destinationId = ReadFromLoRa<unsigned int>();

  LORA_LOG_LN("Sender : " + String(senderId));
  LORA_LOG_LN("Destination : " + String(destinationId));

  // If the packet is not for me, ignore it
  if (destinationId != networkId) {
    LORA_LOG_LN("Ignoring packet : not destined to me");
    ClearBytes(packetSize - 8);
    return;
  }

  // Get the packet number
  unsigned int thisPacketNumber = ReadFromLoRa<unsigned int>();
  LORA_LOG_LN("Packet number : " + String(thisPacketNumber));

  // If the packet has already been received, ignore it
  if (thisPacketNumber == receivedPacketNumber) {
    LORA_LOG_LN("Ignoring packet : packet already received");
    ClearBytes(packetSize - 12);
    return;
  }
  receivedPacketNumber = thisPacketNumber;

  // Get the request type
  RequestType requestId = (RequestType)LoRa.read();

  if (requestId == DT_RPL) {
    HandleDataReplyPacket();
    return;
  }

  // If the request method is unknown, inore the packet
  LORA_LOG_LN("Ignoring packet : unknown request (0x");
  LORA_LOG_HEX(requestId);
  LORA_LOG_LN(")");
  ClearBytes(packetSize - 13);
}


// Read an incoming data reply request
void HandleDataReplyPacket() {
  Measure measure = ReadFromLoRa<Measure>();

  onGetMeasureCallback(measure);
}


// Discards a given amount of data received by LoRa
void ClearBytes(unsigned int length) {
  for (size_t i = 0; i < length; i++)
  {
    LoRa.read();
  }
}


// Reads an object in binary from LoRa
template<typename T>
T ReadFromLoRa() {
  char bytes[sizeof(T)];

  for (size_t i = 0; i < sizeof(T); i++)
  {
    bytes[i] = static_cast<char>(LoRa.read());
  }
  
  return *reinterpret_cast<T*>(&bytes);
}


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
bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, RequestType requestType) {
  LORA_LOG_LN("Sending packet to " + String(destinationId) + "(" + String(payloadSize) + " bytes)");
  LORA_LOG("Request type : ");
  LORA_LOG_HEX(requestType);
  LORA_LOG("\n");

  bool success = (bool)LoRa.beginPacket();
  if (!success) {
    LORA_LOG_LN("Aborting transmission : LoRa module busy");
    return false;
  }

  LoRa.write(reinterpret_cast<uint8_t*>(&networkId), sizeof(networkId));
  LoRa.write(reinterpret_cast<uint8_t*>(&destinationId), sizeof(destinationId));
  LoRa.write(reinterpret_cast<uint8_t*>(&sentPacketNumber), sizeof(sentPacketNumber));
  LoRa.write(reinterpret_cast<uint8_t*>(&requestType), sizeof(requestType));
  LoRa.write(reinterpret_cast<const uint8_t*>(payload), payloadSize);

  success = (bool)LoRa.endPacket();
  if (!success) {
    LORA_LOG_LN("Transmission failed");
  }

  // Set the module back to receive mode
  LoRa.receive();

  sentPacketNumber++;

  return success;
}


#endif