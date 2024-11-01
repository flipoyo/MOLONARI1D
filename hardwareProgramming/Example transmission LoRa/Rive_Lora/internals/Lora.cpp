#include "Lora.hpp"

// Constructor: Set pin and frequency for the LoRa module
LoraCommunication::LoraCommunication(long frequency, uint8_t localAddress)
    : freq(frequency), localAddress(localAddress), active(false) {
        LoRa.enableCrc();
    }

void LoraCommunication::startLoRa()
{
    if (!active)
    {
        int retries = 3;
        while (retries--)
        {
            if (LoRa.begin(freq))
            {
                active = true;
                Serial.println("LoRa started.");
                return;
            }
            else
            {
                Serial.println("LoRa failed to start, retrying...");
                delay(1000); // Delay before retrying
            }
        }
        Serial.println("Starting LoRa failed after retries.");
    }
}

void LoraCommunication::stopLoRa()
{
    if (active)
    {
        LoRa.end();
        active = false;
        Serial.println("LoRa stopped.");
    }
}

void LoraCommunication::sendPacket(const uint8_t &destination, uint8_t packetNumber, RequestType requestType, const String &payload)
{
    if (active)
    {
        // Flush LoRa buffer to clear any residual data
        uint8_t t = requestType;
        delay(100); // Small delay to ensure buffer is cleared
        LoRa.beginPacket();
        LoRa.write(destination);
        LoRa.write(localAddress);
        LoRa.write(packetNumber);
        LoRa.write(requestType);
        LoRa.write(payload.length()); // Ensure packet length is specified
        LoRa.print(payload);
        LoRa.endPacket();
        Serial.print("Packet sent: ");
        Serial.println(payload);
    }
    else
    {
        Serial.println("LoRa is not active, cannot send packet.");
    }
}

bool LoraCommunication::receivePacket(uint8_t &sender, uint8_t &packetNumber, RequestType &requestType, String &payload)
{
    if (!active)
        return false;
    delay(50);
    int ackTimeout = 2000;
    unsigned long startTime = millis();
    while (millis() - startTime < ackTimeout)
    {
        int packetSize = LoRa.parsePacket();
        if (packetSize)
        {
            int recipient = LoRa.read();
            sender = LoRa.read();
            packetNumber = LoRa.read();
            requestType = static_cast<RequestType>(LoRa.read());
            uint8_t incomingLength = LoRa.read(); // Get payload length

            payload = "";
            while (LoRa.available())
            {
                payload += (char)LoRa.read();
            }

            if (incomingLength != payload.length())
            {
                Serial.println("Error: message length mismatch.  Message length: " + String(incomingLength) + "Message: " + payload);
                Serial.println();
                return false; // Exit on length error
            }

            if (recipient != localAddress && recipient != 0xFF)
            {
                Serial.println("This message is not for me. Sent to: 0x" + String(recipient, HEX));
                Serial.println();
                return false; // Ignore packet if not for this device
            }

            Serial.println("Received from: 0x" + String(sender, HEX));
            Serial.println("Sent to: 0x" + String(recipient, HEX));
            Serial.println("Packet Number ID: " + String(packetNumber));
            Serial.println("Packet requestType : " + String(requestType,HEX)+ "  " + String(requestType == SYN));
            Serial.println("Message length: " + String(incomingLength));
            Serial.println("Message: " + payload);
            Serial.println("RSSI: " + String(LoRa.packetRssi()));
            Serial.println("Snr: " + String(LoRa.packetSnr()));
            Serial.println();

            return true;
        }
    }
    return false; // Return false if no packet received within timeout
}

bool LoraCommunication::isLoRaActive()
{
    return active;
}
