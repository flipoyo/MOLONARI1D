// This file will contain all functions relative to LoRa communication

// Check that the file has not been imported before
#ifndef MY_LORA
#define MY_LORA


#include "Lora.hpp"
#include "Reader.hpp"


// Debug methods to enable or disable logging
#ifdef LORA_DEBUG
#define PRINT(msg) Serial.print(msg)
#define PRINT_HEX(msg) Serial.print(msg, HEX)
#define PRINT_LN(msg) Serial.println(msg)
#else
#define PRINT(msg)
#define PRINT_HEX(msg)
#define PRINT_LN(msg)
#endif



// ----- Public functions -----

// Initialise the lora module for the first time. Call before any other LoRa function
template<uint8_t CLIENT_COUNT>
void LoraDeviceClass<CLIENT_COUNT>::Initialise(float frequency) {
  this->frequency = frequency;
  LoRa.begin(frequency);

  LoRa.enableCrc();

  LoRa.onReceive(this->OnReceivePacket);
  LoRa.receive();
}


// Temporarily disable the LoRa module to save battery. It can be waken up with WakeUpLora
template<uint8_t CLIENT_COUNT>
void LoraDeviceClass<CLIENT_COUNT>::Sleep() {
  LoRa.end();

  // Disable the LoRa module to save battery
  // Note : this also resets all the settings of the module
  pinMode(LORA_RESET, OUTPUT);
  digitalWrite(LORA_RESET, LOW);
}


// Re-enable the LoRa module if it was asleep. I.E. Exit low-power mode for the LoRa module
template<uint8_t CLIENT_COUNT>
void LoraDeviceClass<CLIENT_COUNT>::WakeUp() {
  // TODO : test that this works
  // Re-initialise the LoRa module since it has been reset
  this->Initialise(frequency);
}


// ----- Internal functions -----

// Callback function when the lora module receives a packet
// Arguments :
//  packetSize -> Size of the received packet
template<uint8_t CLIENT_COUNT>
void LoraDeviceClass<CLIENT_COUNT>::OnReceivePacket(int packetSize) {
  PRINT_LN("Receiving packet");

  LoraPacket<256> packet;
  bool success = TryReadPacket<256>(packet, packetSize);

  if (!success) {
    return;
  }

  if (packet.receiverId != networkId) {
    PRINT_LN("Packet not for me");
    return;
  }

  LoraClient client;
  success = TryGetLoraClient(client, packet.senderId);

  if (!success) {
    PRINT_LN("Unknown sender (n°" + String(packet.senderId) + ")");
    return;
  }

  if (packet.requestType == DT_REQ) {
    client.HandleRequest(packet);
  }
}


// Discards a given amount of data received by LoRa
template<uint8_t CLIENT_COUNT>
void LoraDeviceClass<CLIENT_COUNT>::ClearBytes(unsigned int length) {
  for (size_t i = 0; i < length; i++)
  {
    LoRa.read();
  }
}


// Sends a data packet through LoRa
// Arguments :
//  payload -> A pointer to the object to send (&obj)
//  payloadSize -> The size of the object to send (sizeof(obj))
//  destinationId -> The address of the destination device of the message
//  requestType -> The type of packet request to send
// Example :
//  SendPacket(&data, sizeof(data), destId, DT_REQ)
template<uint8_t CLIENT_COUNT>
bool LoraDeviceClass<CLIENT_COUNT>::SendPacket(const void* payload, unsigned int payloadSize, unsigned int destinationId, unsigned int sentPacketNumber, RequestType requestType) {
  PRINT_LN("Sending packet to " + String(destinationId) + "(" + String(payloadSize) + " bytes)");
  PRINT("Request type : ");
  PRINT_HEX(requestType);
  PRINT("\n");

  bool success = (bool)LoRa.beginPacket();
  if (!success) {
    PRINT_LN("Aborting transmission : LoRa module busy");
    return false;
  }

  LoRa.write(reinterpret_cast<uint8_t*>(&networkId), sizeof(networkId));
  LoRa.write(reinterpret_cast<uint8_t*>(&destinationId), sizeof(destinationId));
  LoRa.write(reinterpret_cast<uint8_t*>(&sentPacketNumber), sizeof(sentPacketNumber));
  LoRa.write(reinterpret_cast<uint8_t*>(&requestType), sizeof(requestType));
  LoRa.write(reinterpret_cast<uint8_t*>(&payloadSize), sizeof(payloadSize));
  LoRa.write(reinterpret_cast<const uint8_t*>(payload), payloadSize);

  success = (bool)LoRa.endPacket();
  if (!success) {
    PRINT_LN("Transmission failed");
  }

  // Set the module back to receive mode
  LoRa.receive();

  sentPacketNumber++;

  return success;
}


template<uint8_t CLIENT_COUNT>
template<uint16_t PAYLOAD_CAPACITY>
bool LoraDeviceClass<CLIENT_COUNT>::TryReadPacket(LoraPacket<PAYLOAD_CAPACITY>& packet, int packetSize) {
    // Reject packets that are too small to have a valid header
    if (packetSize < sizeof(LoraPacket<0>)) {
      PRINT_LN("Ignoring packet : too small to have a valid header (size = " + String(packetSize) + ")");
      ClearBytes(packetSize);
      return false;
    }

    // Reject packets that are too big
    if (packetSize > sizeof(LoraPacket<PAYLOAD_CAPACITY>)) {
      PRINT_LN("Ignoring packet : too big to fit into allocated memory (size = " + String(packetSize) + ")");
      ClearBytes(packetSize);
      return false;
    }

    // Read the packet
    LoRa.readBytes(reinterpret_cast<uint8_t*>(&packet), packetSize);
    return true;
}


template<uint8_t CLIENT_COUNT>
bool LoraDeviceClass<CLIENT_COUNT>::TryGetClient(LoraClient& client, unsigned int remoteId) {
  for (int i = 0; i < CLIENT_COUNT; i++) {
    if (this->clients[i].remoteId == remoteId) {
      client = this->clients[i];
      return true;
    }
  }

  return false;
}


#endif