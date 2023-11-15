// This file will contain all functions relative to LoRa communication

// Check that the file has not been imported before
#ifndef MY_LORA
#define MY_LORA


#include "Lora.hpp"
#include "Reader.hpp"


// Debug methods to enable or disable logging
#ifdef LORA_DEBUG
#define LOG(msg) Serial.print(msg)
#define LOG_HEX(msg) Serial.print(msg, HEX)
#define LOG_LN(msg) Serial.println(msg)
#else
#define LOG(msg)
#define LOG_HEX(msg)
#define LOG_LN(msg)
#endif



// ----- Public functions -----

// Initialise the lora module for the first time. Call before any other LoRa function
void InitialiseLora(float frequency) {
  _frequency = frequency;
  LoRa.begin(frequency);

  LoRa.enableCrc();
  sentPacketNumber = LoRa.random();

  LoRa.onReceive(OnLoraReceivePacket);
  LoRa.receive();
}


// Temporarily disable the LoRa module to save battery. It can be waken up with WakeUpLora
void SleepLora() {
  LoRa.end();

  // Disable the LoRa module to save battery
  // Note : this also resets all the settings of the module
  pinMode(LORA_RESET, OUTPUT);
  digitalWrite(LORA_RESET, LOW);
}


// Re-enable the LoRa module if it was asleep. I.E. Exit low-power mode for the LoRa module
void WakeUpLora() {
  // TODO : test that this works
  // Re-initialise the LoRa module since it has been reset
  InitialiseLora(_frequency);
}


// ----- Internal functions -----

// Callback function when the lora module receives a packet
// Arguments :
//  packetSize -> Size of the received packet
void OnLoraReceivePacket(int packetSize) {
  LOG_LN("Receiving packet");

  // If the header is incomplete, ignore the packet
  if (packetSize < 13) {
    LOG_LN("Ignoring packet : wrong size");
    ClearBytes(packetSize);
    return;
  }

  // Get sender and destination
  unsigned int senderId = ReadFromLoRa<unsigned int>();
  unsigned int destinationId = ReadFromLoRa<unsigned int>();

  LOG_LN("Sender : " + String(senderId));
  LOG_LN("Destination : " + String(destinationId));

  // If the packet is not for me, ignore it
  if (destinationId != networkId) {
    LOG_LN("Ignoring packet : not destined to me");
    ClearBytes(packetSize - 8);
    return;
  }

  // Get the packet number
  unsigned int thisPacketNumber = ReadFromLoRa<unsigned int>();
  LOG_LN("Packet number : " + String(thisPacketNumber));

  // If the packet has already been received, ignore it
  if (thisPacketNumber == receivedPacketNumber) {
    LOG_LN("Ignoring packet : packet already received");
    ClearBytes(packetSize - 12);
    return;
  }
  receivedPacketNumber = thisPacketNumber;

  // Get the request type
  RequestType requestId = (RequestType)LoRa.read();

  if (requestId == DT_REQ) {
    LOG_LN("Data requested");
    HandleDataRequest(senderId);
    return;
  }

  // If the request method is unknown, inore the packet
  LOG_LN("Ignoring packet : unknown request (0x");
  LOG_HEX(requestId);
  LOG_LN(")");
  ClearBytes(packetSize - 13);
}


// Respond to an incoming data request
void HandleDataRequest(unsigned int senderId) {
  unsigned int requestedSampleId = ReadFromLoRa<uint32_t>();
  LOG_LN("Sample requested from : " + String(requestedSampleId));

  Reader reader = Reader();
  reader.EstablishConnection();
  reader.MoveCursor(requestedSampleId);

  LOG_LN("Sending samples ...");
  while (reader.IsDataAvailable()) {
    Measure measure = reader.ReadMeasure();
    LOG_LN(measure.ToString());
    SendMeasurement(measure, senderId);
  }
  LOG_LN("Done");
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
// Arguments :
//  payload -> A pointer to the object to send (&obj)
//  payloadSize -> The size of the object to send (sizeof(obj))
//  destinationId -> The address of the destination device of the message
//  requestType -> The type of packet request to send
// Example :
//  SendPacket(&data, sizeof(data), destId, DT_REQ)
bool SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, RequestType requestType) {
  LOG_LN("Sending packet to " + String(destinationId) + "(" + String(payloadSize) + " bytes)");
  LOG("Request type : ");
  LOG_HEX(requestType);
  LOG("\n");

  bool success = (bool)LoRa.beginPacket();
  if (!success) {
    LOG_LN("Aborting transmission : LoRa module busy");
    return false;
  }

  LoRa.write(reinterpret_cast<uint8_t*>(&networkId), sizeof(networkId));
  LoRa.write(reinterpret_cast<uint8_t*>(&destinationId), sizeof(destinationId));
  LoRa.write(reinterpret_cast<uint8_t*>(&sentPacketNumber), sizeof(sentPacketNumber));
  LoRa.write(reinterpret_cast<uint8_t*>(&requestType), sizeof(requestType));
  LoRa.write(reinterpret_cast<const uint8_t*>(payload), payloadSize);

  success = (bool)LoRa.endPacket();
  if (!success) {
    LOG_LN("Transmission failed");
  }

  // Set the module back to receive mode
  LoRa.receive();

  sentPacketNumber++;

  return success;
}


// Sends a measurement (DT_RPL) via LoRa
// Arguments :
//  measure -> The measurement to send
//  destinationId -> The address of the destination device of the message 
bool SendMeasurement(Measure measure, unsigned int destinationId) {
  LOG_LN("Sending measurement n°" + String(measure.id));
  return SendPacket(&measure, sizeof(measure), destinationId, DT_RPL);
}


#endif