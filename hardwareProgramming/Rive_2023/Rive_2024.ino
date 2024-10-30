#include "internals/Lora.hpp"
#include <queue>

uint8_t localAddress = 0xbb;
LoraCommunication lora(868E6, localAddress);
std::queue<String> receiveQueue;

const int MAX_QUEUE_SIZE = 255;  // Queue size limit for the receiver

void setup() {
    Serial.begin(9600);
    while (!Serial);
    lora.startLoRa();
    Serial.println("Receiver ready...");
}

void endSessionAndPrintQueue() {
    Serial.println("Session ended. Printing all received data:");
    //send fin ack to be add
    while (!receiveQueue.empty()) {
        Serial.println(receiveQueue.front());  // Print the front item in the queue
        receiveQueue.pop();                    // Remove item from the queue
    }
    Serial.println("All data printed. Queue is now empty.");
}

void loop() {
    uint8_t dest, packetNumber = 0;
    String payload;
    RequestType requestType;
    uint8_t previous_packetNumber = 0;

    while (true) {
        if (lora.receivePacket(dest, packetNumber, requestType, payload)){
            switch (requestType) {
                case SYN:
                    lora.sendPacket(dest, 0, SYN, "SYN-ACK");
                    Serial.println("SYN-ACK sent.");
                    break;
                case ACK:
                    Serial.println("Handshake complete. Ready to receive data.");
                    break;
                case FIN:
                    lora.sendPacket(dest, packetNumber, FIN, "FIN-ACK");
                    Serial.println("FIN received, session closing.");
                    endSessionAndPrintQueue();  // Print queue contents after session ends
                    lora.stopLoRa();
                    delay(1000);
                    lora.startLoRa();
                    Serial.println("Ready for new session.");
                    return;  // End loop to reset the session
                default:
                    if (receiveQueue.size() >= MAX_QUEUE_SIZE) {
                        Serial.println("Queue full, sending FIN to close session.");
                        lora.sendPacket(dest, packetNumber, FIN, "");  // Close session
                        endSessionAndPrintQueue();  // Print queue contents if full
                        lora.stopLoRa();
                        delay(1000);
                        lora.startLoRa();
                        Serial.println("Ready for new session.");
                        return;  // End loop to reset the session
                    }
                    if(previous_packetNumber == packetNumber){
                      lora.sendPacket(dest, packetNumber, ACK, "ACK");
                      break;
                    }
                    previous_packetNumber = packetNumber;
                    receiveQueue.push(payload);  // Add received data to the queue
                    lora.sendPacket(dest, packetNumber, ACK, "ACK");
                    Serial.println("ACK sent for packet " + String(packetNumber));
                    break;
            }
        }
    }
}
