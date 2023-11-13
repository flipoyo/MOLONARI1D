#ifndef LORA_CLIENT_HPP
#define LORA_CLIENT_HPP

#include "Lora.hpp"
#include "LoraPacket.hpp"
#include "Measure.hpp"


class LoraClient {
public:
  // The nework ID of the remote device
  const unsigned int remoteId;

  // Constructor
  LoraClient() : remoteId(0) {}
  LoraClient(unsigned int _remoteId) : remoteId(_remoteId) {}

  template<uint16_t PAYLOAD_CAPACITY>
  void HandleRequest(LoraPacket<PAYLOAD_CAPACITY> packet) {
    if (packet.packetNumber <= receivedPacketNumber) {
      PRINT_LN("Packet already received");
      return;
    }
    receivedPacketNumber = packet.packetNumber;

    switch (packet.requestType)
    {
    case DT_REQ:
      HandleDataRequest<PAYLOAD_CAPACITY>(packet);
      break;
    
    default:
      break;
    }
  }

  template<uint16_t PAYLOAD_CAPACITY>
  void HandleDataRequest(LoraPacket<PAYLOAD_CAPACITY> packet) {
    if (packet.payloadSize != sizeof(uint32_t)) {
      PRINT_LN("Invalid data request packet : invalid payload size (expected " + String(sizeof(uint32_t)) + ", got " + String(packet.payloadSize) + ")");
      return;
    }
    uint32_t requestedSampleId = packet.Read<uint32_t>(0);

    Reader reader = Reader();
    reader.EstablishConnection();
    reader.MoveCursor(requestedSampleId);

    PRINT_LN("Sending samples ...");
    while (reader.IsDataAvailable()) {
      Measure measure = reader.ReadMeasure();
      PRINT_LN(measure.ToString());
      SendMeasurement(measure, senderId);
    }
    PRINT_LN("Done");
  }

  bool SendPacket(const void* payload, unsigned int payloadSize, RequestType requestType) {
    bool success = LoraDevice.SendPacket(payload, payloadSize, remoteId, sentPacketNumber, requestType);
    sentPacketNumber++;

    return success;
  }

  bool SendMeasurement(Measure measure) {
    PRINT_LN("Sending measurement n°" + String(measure.id));
    return SendPacket(&measure, sizeof(measure), DT_RPL);
  }

private:
  // The id number of the last packet received
  unsigned int receivedPacketNumber = 0;
  // The id number of the next packet that will be sent
  unsigned int sentPacketNumber = 0;
};

#endif // LORA_CLIENT_HPP