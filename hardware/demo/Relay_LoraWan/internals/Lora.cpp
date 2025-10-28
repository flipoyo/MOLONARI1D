#include "Lora.hpp"

#ifdef LORA_DEBUG
#define LORA_LOG(msg) Serial.print(msg);
#define LORA_LOG_HEX(msg) Serial.print(msg, HEX);
#define LORA_LOG_LN(msg) Serial.println(msg);
#else
#define LORA_LOG(msg)
#define LORA_LOG_HEX(msg)
#define LORA_LOG_LN(msg)
#endif
// Constructor: Set pin and frequency for the LoRa module
LoraCommunication::LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti)
    : freq(frequency), localAddress(localAdd), destination(desti), active(false)
{
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
                LORA_LOG_LN("LoRa started.");
                return;
            }
            else
            {
                LORA_LOG_LN("LoRa failed to start, retrying...");
                delay(1000); // Delay before retrying
            }
        }
        LORA_LOG_LN("Starting LoRa failed after retries.");
    }
}

void LoraCommunication::stopLoRa()
{
    if (active)
    {
        LoRa.end(); // This internally calls LoRa.sleep() and stops SPI

        // Step 3: Pull the RESET pin low to cut power if connected directly
        pinMode(LORA_RESET, OUTPUT);
        digitalWrite(LORA_RESET, LOW);
        active = false;
        LORA_LOG_LN("LoRa stopped.");
    }
}

void LoraCommunication::setdesttodefault()
{
    if (destination != 0xff)
        destination = 0xff;
}

void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload)
{
    if (active)
    {
        uint8_t b = LoRa.random();
        delay(100 + b); // Small delay to ensure buffer is cleared // Small delay to ensure buffer is cleared

        bool success = (bool)LoRa.beginPacket();
        if (!success)
        {
            LORA_LOG_LN("Aborting transmission : LoRa module busy");
            return;
        }
        // Calculate and append a simple checksum
        uint8_t checksum = calculateChecksum(destination, localAddress, packetNumber, requestType, payload);
        LoRa.write(checksum);

        LoRa.write(destination);
        LoRa.write(localAddress);
        LoRa.write(packetNumber);
        LoRa.write(requestType);
        //LoRa.write(payload.length()); // Specify payload length
        LoRa.print(payload);

        LoRa.endPacket();

        LORA_LOG("Packet sent: ");
        LORA_LOG_LN(payload);
    }
    else
    {
        LORA_LOG_LN("LoRa is not active, cannot send packet.");
    }
}

bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload)
{
    if (!active)
        return false;

    delay(80); // Small delay for synchronization
    int ackTimeout = 2000;
    unsigned long startTime = millis();

    while (millis() - startTime < ackTimeout)
    {
        int packetSize = LoRa.parsePacket();
        if (packetSize)
        {
            uint8_t receivedChecksum = LoRa.read(); // Read the checksum byte
            uint8_t recipient = LoRa.read();
            uint8_t dest = LoRa.read();
            packetNumber = LoRa.read();
            requestType = static_cast<RequestType>(LoRa.read());
           // uint8_t incomingLength = LoRa.read(); // Get payload length

            payload = "";
            while (LoRa.available())
            {
                payload += (char)LoRa.read();
            }

            /*// Verify length
            if (incomingLength != payload.length())
            {
                Serial.println("Error: message length mismatch. Expected: " + String(incomingLength) + ", Actual: " + String(payload.length()));
                return false;
            }*/

            // Verify destination
            if (!isValidDestination(recipient, dest, requestType))
            {
                LORA_LOG_LN("Message is not for this device or is out of session.");
                return false;
            }

            // Verify checksum
            uint8_t calculatedChecksum = calculateChecksum(recipient, dest, packetNumber, requestType, payload);
            if (calculatedChecksum != receivedChecksum)
            {
                LORA_LOG_LN("Checksum mismatch: packet discarded.");
                return false;
            }

            // Log received packet details
            LORA_LOG_LN("Received from: 0x" + String(dest, HEX));
            LORA_LOG_LN("Sent to: 0x" + String(recipient, HEX));
            LORA_LOG_LN("Packet Number ID: " + String(packetNumber));
            LORA_LOG_LN("Packet requestType: " + String(requestType));
           // Serial.println("Message length: " + String(incomingLength));
            LORA_LOG_LN("Message: " + payload);
            LORA_LOG_LN("RSSI: " + String(LoRa.packetRssi()));
            LORA_LOG_LN("SNR: " + String(LoRa.packetSnr()));
            LORA_LOG_LN();

            return true;
        }
    }
    return false; // Return false if no packet received within timeout
}

// Helper function to validate the destination of incoming packets
bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType)
{
    if (recipient != localAddress)
    {
        return false; // Not for this device
    }
    if (destination == dest || (requestType == SYN && destination == 0xff && myNet.find(dest) != myNet.end()))
    {
        destination = dest;
        return true;
    }
    return false; // Out of session or invalid destination
}

// Helper function to calculate a simple checksum for data integrity verification
uint8_t LoraCommunication::calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload)
{
    uint8_t checksum = recipient ^ dest ^ packetNumber ^ static_cast<uint8_t>(requestType);
    for (char c : payload)
    {
        checksum ^= c;
    }
    return checksum;
}

bool LoraCommunication::isLoRaActive()
{
    return active;
}

bool LoraCommunication::Handshake(uint8_t shiftback)
{

    String payload;
    uint8_t packetNumber;
    RequestType requestType;

    while (true)
    {
        if (receivePacket(packetNumber, requestType, payload) && requestType == SYN && packetNumber == 0 && destination != 0xff)
        {
            // get from the saved variable//////////////////////
            sendPacket(shiftback, SYN, "SYN-ACK");
            break;
        }
    }

    int retries = 0;
    LORA_LOG_LN("SYN-ACK sent.");
    while (retries < 6)
    {
        if (receivePacket(shiftback, requestType, payload) && requestType == ACK)
        {
            LORA_LOG_LN("Handshake complete. Ready to receive data.");
            return true;
        }
        else
        {
            LORA_LOG_LN("No ACK received, retrying ...");
            uint8_t b = LoRa.random();
            delay(int(b) * (retries + 1));
            sendPacket(shiftback, SYN, "SYN-ACK");
        }
    }

    LORA_LOG_LN("Handshake failed.");
    stopLoRa();
    return false;
}

int LoraCommunication::receivePackets(std::queue<String> &receiveQueue)
{
    uint8_t packetNumber = 0;
    String payload;
    RequestType requestType;
    uint8_t previous_packetNumber = -1;

    int ackTimeout = 60000;
    unsigned long startTime = millis();
    receiveQueue.push(String(destination));

    while (millis() - startTime < ackTimeout)
    {
        if (receivePacket(packetNumber, requestType, payload))
        {
            switch (requestType)
            {
            case FIN:
                LORA_LOG_LN("FIN received, session closing.");
                return packetNumber; // End loop to reset the session
            default:
                if (receiveQueue.size() >= MAX_QUEUE_SIZE)
                {
                    LORA_LOG_LN("Queue full, sending FIN to close session.");
                    return packetNumber; // End loop to reset the session
                }
                if (previous_packetNumber == packetNumber)
                {
                    sendPacket(packetNumber, ACK, "ACK");
                    break;
                }
                previous_packetNumber = packetNumber;
                receiveQueue.push(payload); // Add received data to the queue
                sendPacket(packetNumber, ACK, "ACK");
                LORA_LOG_LN("ACK sent for packet " + String(packetNumber));
                break;
            }
        }
    }
    LORA_LOG_LN("Connection lost at packetNumber: " + String(packetNumber));
}

void LoraCommunication::closeSession(int lastPacket)
{
    sendPacket(lastPacket, FIN, "");
    LORA_LOG_LN("FIN sent, waiting for final ACK...");

    String payload;
    uint8_t packetNumber;
    RequestType requestType;
    int retries = 0;

    while (retries < 3)
    {
        if (receivePacket(packetNumber, requestType, payload) && requestType == FIN && packetNumber == lastPacket)
        {
            LORA_LOG_LN("Final ACK received, session closed.");

            return;
        }
        else
        {
            LORA_LOG_LN("No final ACK, retrying...");
            uint8_t b = LoRa.random();
            delay(int(b) * (retries + 1));
            sendPacket(lastPacket, FIN, "");
            retries++;
        }
    }
    LORA_LOG_LN("Session closure failed after retries.");
}
