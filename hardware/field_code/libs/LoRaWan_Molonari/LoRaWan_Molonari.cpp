// LoRaWan_Molonari.cpp
// This file defines the LoraWANCommunication class for handling LoRaWAN communication.

#include "LoRaWan_Molonari.hpp"
#include <Reader.hpp>

#ifdef LORA_DEBUG
#define LORA_LOG(msg) Serial.print(msg);
#define LORA_LOG_HEX(msg) Serial.print(msg, HEX);
#define LORA_LOG_LN(msg) Serial.println(msg);
#else
#define LORA_LOG(msg)
#define LORA_LOG_HEX(msg)
#define LORA_LOG_LN(msg)
#endif

LoraWANCommunication::LoraWANCommunication() {}

bool LoraWANCommunication::begin(const String& appEui, const String& appKey) {
    if (!modem.begin(EU868)) {
        Serial.println("Échec initialisation module LoRaWAN");
        return false;
    }

    int connected = modem.joinOTAA(appEui, appKey);
    if (!connected) {
        Serial.println("Échec de la connexion LoRaWAN");
        return false;
    }

    modem.minPollInterval(60);
    modem.setADR(true);
    return true;
}

bool LoraWANCommunication::sendQueue(std::queue<String>& sendingQueue) {
    while (!sendingQueue.empty()) {
        String payload = sendingQueue.front();
        int err = 0, retries = 0;
        do {
            modem.beginPacket();
            modem.print(payload);
            err = modem.endPacket(true);
            if (err <= 0) {
                Serial.println("payload : " + payload);
                Serial.println("Erreur d’envoi, nouvelle tentative...");
                delay(10000);
            }
        } while (err <= 0 && ++retries < 6);

        if (err > 0) {
            Serial.println("Donnée envoyée : " + payload);
            sendingQueue.pop();
        } else {
            Serial.println("Échec après plusieurs tentatives, abandon du paquet.");
            return false;
        }
        delay(5000);
    }
    return true;
}



bool LoraWANCommunication::sendAllPacketsAndManageMemoryWAN(std::queue<memory_line>& sendQueue, unsigned long& SDOffset, File& dataFile) {
    // handles packet sending and acknowledgement verificaiton, SDOffset updating, and ensures dataFile.position() is at the right place (terminal SDOffset).

    uint8_t nb_packets_sent = 0;
    String payload; uint8_t nb_packets_sent_received;

    while (!sendQueue.empty()) {

        memory_line packet = sendQueue.front();
        Serial.println("packet dans sendAllPacketsAndManageMemoryWAN : " + packet.flush);
        int send_retries = 0;
        int err = 0;
        while(send_retries < 2 && err <= 0){ //remettre send_retries à 10 après test
            modem.beginPacket();
            modem.print(payload);

            int err = modem.endPacket(true);
            if (err <= 0) {
                Serial.println("payload : " + payload);
                Serial.println("Erreur d’envoi, nouvelle tentative...");
                delay(1000);//remettre à 10 000 après les tetst
            }
            send_retries++;
        }
    
        if (err > 0) {
            Serial.println("Donnée envoyée : " + payload);
            sendQueue.pop();
            SDOffset = packet.memory_successor;

        } else {
            Serial.println("Échec après plusieurs tentatives, abandon du paquet.");
            dataFile.seek(SDOffset);
            return false;
        }
        delay(5000);

    }
    dataFile.seek(SDOffset);
    return true;
}



bool LoraWANCommunication::receiveConfig(const char* configFilePath, bool modif) {
    String rcv = modem.readString();
    Serial.print("↓ Message reçu en downlink : ");
    Serial.println(rcv);

    const char* tmpPath = "tmp_conf.csv";
    File tmp = SD.open(tmpPath, FILE_WRITE | O_TRUNC);
    tmp.println(rcv);
    tmp.close();
    
    File newF = SD.open(configFilePath, FILE_WRITE | O_TRUNC);
    if (!newF) {
        Serial.print("Impossible de créer ");
        Serial.println(configFilePath);
        return false;
    }
    File tmpRead = SD.open(tmpPath, FILE_READ);
    if (!tmpRead) {
        Serial.println("Impossible d'ouvrir tmp pour lecture");
        newF.close();
        return false;
    }
    while (tmpRead.available()) {
        newF.write(tmpRead.read());
    }
    tmpRead.close();
    newF.close();
    SD.remove(tmpPath);
    return true;

}

