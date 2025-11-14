# **Presentation of libraries**

This document presents the various libraries used in the Molonari project for In the Air applications, as well as their basic operation with diagrams. 

## *LoRa_Molonari*
LoRa_Molonari is a library enabling wireless communication between two boards via the LoRa protocol: 

- Initialization and management of the LoRa connection: Starting and stopping the LoRa module.
- Sending and receiving packets: With checksum and acknowledgment management.
- Handshake: Establishing a reliable connection between a master and a slave.
- Session closure: Clean termination of communication.



       ┌────────────────────┐
       │ startLoRa()        │
       └────────────────────┘
              │
              ▼
       ┌────────────────────┐
       │ Handshake MASTER   │
       │ SYN → SYN-ACK → ACK│
       └────────────────────┘
              │
              ▼
       ┌────────────────────┐
       │ sendPackets()      │
       │  - sendPacket()    │
       │  - attendre ACK    │
       └────────────────────┘
              │
              ▼
       ┌────────────────────┐
       │ receivePackets()   │
       │  - receivePacket() │
       │  - envoyer ACK     │
       └────────────────────┘
              │
              ▼
       ┌────────────────────┐
       │ closeSession()     │
       │  - envoyer FIN     │
       │  - attendre FIN    │
       └────────────────────┘


## *LoRaWan_Molonari*
LoRaWAN_Molonari is a library that enables data to be sent via the LoRaWAN network:

- OTAA connection: Activation of the LoRaWAN module via AppEUI and AppKey.
- Data transmission: Management of a queue of messages to be sent.
- Error handling: Automatic retry in case of transmission failure.
- Network configuration: Adaptive data rate (ADR) and poll interval.

       ┌────────────────────────┐
       │ Queue of messages      │
       │ (std::queue<String>)   │
       └───────────┬────────────┘
              │
              ▼
       ┌────────────────────────┐
       │ LoraWANCommunication   │
       │ sendQueue()            │
       └────────────────────────┘
              │
              ▼
       ┌────────────────────────┐
       │ Loop on every msg      │
       │  - beginPacket()       │
       │  - print(payload)      │
       │  - endPacket()         │
       └────────────────────────┘
              │
              ▼
       ┌────────────────────────┐
       │ Check error            │
       │  - if ok : delete.     │
       │  - else : retry (max6) │
       └────────────────────────┘
              │
              ▼
       ┌────────────────────────┐
       │ Transmission sucess ?  │
       │  - Yes → log message   │
       │  - No  → quit msg      │
       └────────────────────────┘



## *Measure*
Measure is a library that allows you to retrieve data from sensors and format it:

- a Sensor class that retrieves data from sensors
- a Measure class that formats the measurements sent to it

The data is returned in the form “ ‘Measure no.’ ID, date, time, measurements” and is then sent to Writer.

                  ┌───────────────────────────┐
                  │        Sensor             │
                  └─────────────┬─────────────┘
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
             ▼                                     ▼
    ┌────────────────────┐                 ┌─────────────────────┐
    │ Default constructor│                 │ Full constructor.   │
    │                    │                 │ with pins, etc... │
    │ (dataPin=-1,...)   │                 │                     │
    └─────────┬──────────┘                 └─────────┬───────────┘
              │                                      │
              └──────────────┐───────────────────────┘
                             ▼
                    ┌────────────────────────────────────┐
                    │ Sensor::Measure                    │
                    │ 1. Active sensor (enablePin HIGH)  │
                    │ 2. Wait 200 ms                     │
                    │ 3. Read analogic on dataPin        │
                    │ 4. Desactivates sensor (LOW)       │
                    │ 5. Return measure (MESURE)         │
                    └─────────┬──────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Measure       │
                    └─────────┬───────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌───────────────────────┐     ┌───────────────────────┐
    │ Measure::oneLine()    │     │ Measure::ToString()   │
    │ - Gets date/hour      │     │ - Prefix "Measure n°" │
    │ - Loop vecteur        │     │ - Call oneLine()      │
    │   channel[] for       │     │ - Return string       │
    │   formatting values.  │     └───────────────────────┘
    │ - Return ligne CSV    │
    └───────────────────────┘


## *Writer*
Writer is a library that allows you to write data to the SD card:

- Connection management (automatic reconnection in case of loss)
- Optional debug logs
- Unique IDs for each measurement
- Standardized CSV formatting and writing to the card



┌───────────────────────────────┐
│          CAPTEURS             │
│ (Measure via Sensor/Measure)  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│          MEASURE              │
│ - Contains values.            │
│ - Formats as CSV (ToString)   │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│           WRITER              │
│                               │
│ LogData()                     │
│ ├─ ApplyContent() → Fills     │
│ │    channels                 │
│ ├─ Check SD connexion.        │
│ ├─ WriteInNewLine() → Write   │
│ │   CSV and flush             │
│ └─ Increments next_id         │
│                               │
│ Reconnect() → Restaure SD if  │
│ loss of connexion             │
│ Dispose() → Close file        │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│             SD                │
│ - Keeps measures as CSV.      │
└───────────────────────────────┘

## *Reader*
Reader is a library that allows you to retrieve data stored on the SD card after it has been written by Writer:

- Read a CSV configuration file for an embedded system (LoRa settings, sensors, etc.)
- Manage a read cursor for a data file (data.csv)
- Load data into a queue for later processing
- Save the cursor position to resume reading after a power failure

                       ┌─────────────────────────────┐
                       │        Reader               │
                       └─────────────┬───────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 ┌─────────────────────┐                           ┌────────────────────────────────┐
 │ lireConfigCSV()     │                           │ SD file operations             │
 │ - Opens file CSV    │                           │ (data.csv, cursor_position.txt)│
 │ - Lit line per      │                           └─────────┬──────────────────────┘
 │   line              │                                     │
 │ - Cuts in tokens    │
 │ - Fills liste_capteurs vector<SensorConfig> 
 └─────────────────────┘
                                     │
                                     ▼
                       ┌──────────────────────────────┐
                       │ EstablishConnection(shift)   │
                       │ - Opens file data.csv        │
                       │ - Gets cursor.               │
                       │ - allows reading             │  
                       └─────────────┬────────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 ┌─────────────────────┐                           ┌─────────────────────────┐
 │ UpdateCursor(shift) │                           │ loadDataIntoQueue()     │
 │ - Moves line_cursor │                           │ - Reads following.      │
 │ - Saves curseur     │                           │   lines dans la SD      │
 │   in cursor.txt     │                           │ - fills queue<String>   │
 └─────────────────────┘                           └─────────┬───────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────────────────┐
                       │ ReadMeasure() / IsDataAvailable()   │
                       │ - Reads following line              │
                       │ - Check disponibility.              │
                       └─────────────┬───────────────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────────┐
                       │ Dispose()                   │
                       │ - close SD file.            │
                       └─────────────────────────────┘

## *Time*
This file manages the time and measurement schedules for the MKR board-based system. It uses both the board's internal clock (RTCZero) and an external clock (RTC_PCF8523) to ensure accuracy and persistence after power loss.
                 ┌──────────────────────────┐
                 │  Read config CSV         │
                 │  (freq_mesure&freq_LoRa) │
                 └─────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Initialisation RTC      │
                  │ internalRtc&externalRtc │
                  └─────────────┬───────────┘
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
          ▼                                           ▼
 ┌─────────────────────┐                     ┌───────────────────────┐
 │ RTC synchro         │                     │ Initialisation vecteur│
 │ intern ↔ extern.    │                     │ measurementTimesVec   │
 └─────────┬───────────┘                     └─────────┬─────────────┘
           │                                           │
           ▼                                           ▼
  ┌─────────────────────┐                   ┌────────────────────────┐
  │ Get date/hour.      │                   │ Calculates time        │
  │ GetCurrentDate/Hour │                   │ since midnight         │
  └─────────┬───────────┘                   └─────────┬──────────────┘
            │                                            │
            ▼                                            ▼
   ┌─────────────────────┐                     ┌───────────────────────┐
   │ Initialises loop    │                     │ Determines next       │
   │ measures            │                     │ measurement time      │
   └─────────┬───────────┘                     └─────────┬─────────────┘
             │                                            │
             └───────────────────┬────────────────────────┘
                                 ▼
                      ┌─────────────────────────┐
                      │ CalculateSleepTimeUntil │
                      │ NextMeasurement()       │
                      │  → return ms until      │
                      │    next measure         │
                      └─────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────────┐
                      │ Microcontroler sleeps   │
                      │ until next              │
                      │ measure (low power)     │
                      └─────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────────┐
                      │ Wakes up and measueres  │
                      │ via Sensor::Measure()   │
                      └─────────────────────────┘
                                 │
                                (loop)

## *Waiter*
This file manages the wait time and task synchronization for the Arduino, particularly for LoRa communication and reading/writing to the SD card.
┌─────────────────────────┐
│       Waiter            │
└────────────┬────────────┘
             │
             ▼
      ┌───────────────┐
      │ startTimer()  │
      │ - remembers t0│
      └───────────────┘
             │
             ▼
      ┌───────────────┐
      │ sleepUntil()  │
      │ - calculates  │
      │ - deepSleep   │
      └───────────────┘
             │
             ▼
      ┌───────────────┐
      │ delayUntil()  │
      └───────────────┘
             │
 ┌───────────┴───────────┐
 │      Loop active      │
 └───────────┬───────────┘
             │
   ┌─────────┴─────────┐
   │ LoRa communication│
   │ - startLoRa()     │
   │ - handshake()     │
   │ - sendPackets()   │
   │ - closeSession()  │
   │ - stopLoRa()      │
   └─────────┬─────────┘
             │
   ┌─────────┴───────────────┐
   │ SD Reader               │
   │ - EstablishConnection() │
   │ - loadDataIntoQueue()   │
   │ - UpdateCursor()        │
   │ - Dispose()             │
   └─────────┬───────────────┘
             │
             ▼
      ┌───────────────┐
      │ PrintQueue()  │
      │ - show and.   │
      │   empty queue │
      └───────────────┘

