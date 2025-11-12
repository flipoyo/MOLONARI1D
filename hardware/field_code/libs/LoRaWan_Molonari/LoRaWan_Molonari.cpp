// LoRaWan_Molonari.cpp
// This file defines the LoraWANCommunication class for handling LoRaWAN communication.
#include <pb.h>
#include <pb_common.h>
#include <pb_decode.h>
#include <pb_encode.h>
#include <MKRWAN.h>
#include "encode.h"

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
    Serial.println("appKey : " + appKey);
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


bool encode(uint8_t *outBuffer, size_t outSize, size_t &messageLength, String inputLine) {
    SensorData msg = SensorData_init_zero;

    // Exemple :
    // "ua4aef7; 27 ; 10/11/2025 ; 16:01:25 ; 1299.00; 1289.00; 1978.00; 1868.00; 2586.00; 2594.00;"
    inputLine.trim();

    String dateStr = "";
    String timeStr = "";

    // --- Découpage de la ligne ---
    int fieldIndex = 0;
    int startIndex = 0;

    while (true) {
        int sepIndex = inputLine.indexOf(';', startIndex);
        if (sepIndex == -1) break;
        String token = inputLine.substring(startIndex, sepIndex);
        token.trim();

        switch (fieldIndex) {
            case 0: // Identifiant (UI)
                strncpy(msg.UI, token.c_str(), sizeof(msg.UI));
                msg.UI[sizeof(msg.UI) - 1] = '\0';
                break;

            case 1: // Numéro de mesure
                break;

            case 2: // Date
                dateStr = token;
                break;

            case 3: // Heure
                timeStr = token;
                break;

            default: // Les mesures
                msg.measurements[msg.measurements_count] = token.toFloat();
                msg.measurements_count++;
                break;
        }

        fieldIndex++;
        startIndex = sepIndex + 1;
    }

    // --- Conversion date+heure vers format compact ---
    // Exemple : "10/11/2025" + "16:01:25" → "1110251601"
    int jour = 0, mois = 0, annee = 0;
    int heure = 0, minute = 0, seconde = 0;

    sscanf(dateStr.c_str(), "%d/%d/%d", &jour, &mois, &annee);
    sscanf(timeStr.c_str(), "%d:%d:%d", &heure, &minute, &seconde);

    // On prend seulement les deux derniers chiffres de l’année
    int annee2 = annee % 100;

    // On concatène dans l’ordre : MM JJ AA HH MM → "1110251601"
    char dateTimeStr[11];
    snprintf(dateTimeStr, sizeof(dateTimeStr), "%02d%02d%02d%02d%02d",
             mois, jour, annee2, heure, minute);

    msg.time = strtoul(dateTimeStr, nullptr, 10);


    // --- Encodage Protobuf ---
    pb_ostream_t stream = pb_ostream_from_buffer(outBuffer, outSize);
    if (!pb_encode(&stream, SensorData_fields, &msg)) {
        Serial.println("Protobuf encoding error!");
        return false;
    }

    messageLength = stream.bytes_written;
    Serial.print("Binary payload (length ");
    Serial.print(messageLength);
    Serial.println(" bytes) ready to send!");
    return true;
}



/*
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
}*/



bool LoraWANCommunication::sendAllPacketsAndManageMemoryWAN(std::queue<memory_line>& sendQueue, unsigned long& SDOffset, File& dataFile) {
    // handles packet sending and acknowledgement verificaiton, SDOffset updating, and ensures dataFile.position() is at the right place (terminal SDOffset).

    while (!sendQueue.empty()) {
        uint8_t buffer[64];
        size_t messageLength = 0;
        
        memory_line packet = sendQueue.front();
        Serial.print("Sending packet with data: " + packet.flush + "\n");

        if (!encode(buffer, sizeof(buffer), messageLength, packet.flush)) {
            Serial.println("Error, payload pas encodé at all (du tout)");
            delay(10000);
            return false;
        }

        int send_retries = 0;
        int err = 0;
        while(send_retries < 2 && err <= 0){ //remettre send_retries à 10 après test
            modem.beginPacket();


            modem.write(buffer, messageLength);

            err = modem.endPacket(true);
            if (err <= 0) {
                Serial.println("échec d'envoi de : " + packet.flush);
                Serial.println("Erreur d’envoi, nouvelle tentative...");
                delay(1000);//remettre à 10 000 après les tetst
            }
            send_retries++;
        }
    
        if (err > 0) {
            Serial.println("Donnée envoyée : " + packet.flush);
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
