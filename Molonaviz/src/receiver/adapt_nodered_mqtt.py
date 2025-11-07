#!/usr/bin/env python3
"""
chirpstack_mqtt_to_sqlite.py

Objectives :
- Get MQTT TLS connection (cert/key/ca) on a broker (10088 port for ChirpStack)
- Filter messages by DeviceEUI
- Extract fields of interest and insert them in a SQLite DB
- Provide a CSV export function

Usage :
    python chirpstack_mqtt_to_sqlite.py                   # launches the MQTT worker
    python chirpstack_mqtt_to_sqlite.py --export out.csv  # CSV export and exit
"""

from PyQt5.QtSql import QSqlDatabase, QSqlQuery
import json
import logging
import queue
import sys
import threading
import time
import os

import pandas as pd
import paho.mqtt.client as mqtt

from . import decoder
from .db_insertion import insert_payload, createRealDatabase, fillRealDatabase
from src.receiver.logger_timestamps import logger_timestamps

# Load configuration from JSON file
with open(os.path.join(os.path.dirname(__file__), './settings/config.json')) as config_file:
    config = json.load(config_file)

# ---- MQTT configuration ----

MQTT_BROKER = config["mqtt"]["broker"]
MQTT_PORT = config["mqtt"]["port"]
MQTT_TOPIC = config["mqtt"]["topic"]
MQTT_CLIENT_ID = config["mqtt"]["client_id"]
MQTT_KEEPALIVE = config["mqtt"]["keepalive"]

# paths to TLS files
MQTT_CA_CERT = config["mqtt"]["ca_cert"]
MQTT_CLIENT_CERT = config["mqtt"]["client_cert"]
MQTT_CLIENT_KEY = config["mqtt"]["client_key"]

# SQLite DB configuration
DB_FILENAME = config["database"]["filename"]
SQLITE_TABLE = config["database"]["local_table"]
REAL_DB_INSERTION = config["database"]["real_database_insertion"]

DEVICE_EUIS = config["mqtt"]["device_euis"] # list of DeviceEUIs to filter (empty = all devices)

# Queue size for incoming messages (to not block the MQTT callback)
MESSAGE_QUEUE_MAX = config["mqtt"]["message_queue_max"]

# Logging to better control infos and alerts displayed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("chirpstack")

def normalize_eui(eui):
    '''Normalizes a DeviceEUI in lowercase without spaces. Returns None if input is None.'''
    if eui is None:
        return None
    return str(eui).strip().lower()



# ---- Temporary database logic ----

def init_db(db_path=DB_FILENAME):
    '''Initializes the SQLite DB and creates the table if necessary using PyQt5.'''
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(db_path)

    if not db.open():
        if REAL_DB_INSERTION:
            if not createRealDatabase():
                logger.error("Failed to create real database.")
                return None
            return fillRealDatabase()
        else:
            logger.error("Failed to open database: %s", db.lastError().text())
            return None
    elif REAL_DB_INSERTION:
        # Database exists, just return the connection
        return db

    query = QSqlQuery(db)
    query.exec(f'''
    CREATE TABLE IF NOT EXISTS {SQLITE_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_eui TEXT,
        timestamp TEXT,
        relay_id TEXT,
        gateway_id TEXT,
        fcnt INTEGER,
        a0 REAL,
        a1 REAL,
        a2 REAL,
        a3 REAL,
        a4 REAL,
        a5 REAL
    )
    ''')
    if query.lastError().isValid():
        logger.error("Failed to create table: %s", query.lastError().text())
    else:
        logger.info("Table '%s' initialized in DB '%s'", SQLITE_TABLE, db_path)
    return db


def insert_record(db, rec):
    '''Insert a record into the database using PyQt5.'''
    query = QSqlQuery(db)
    query.prepare(f'''
        INSERT INTO {SQLITE_TABLE} (
            device_eui, timestamp, relay_id, gateway_id, fcnt, a0, a1, a2, a3, a4, a5
        ) VALUES (:device_eui, :timestamp, :relay_id, :gateway_id, :fcnt, :a0, :a1, :a2, :a3, :a4, :a5)
    ''')

    query.bindValue(":device_eui", rec.get("device_eui"))
    query.bindValue(":timestamp", rec.get("timestamp"))
    query.bindValue(":relay_id", rec.get("relay_id"))
    query.bindValue(":gateway_id", rec.get("gateway_id"))
    query.bindValue(":fcnt", rec.get("fcnt"))
    query.bindValue(":a0", rec.get("a0"))
    query.bindValue(":a1", rec.get("a1"))
    query.bindValue(":a2", rec.get("a2"))
    query.bindValue(":a3", rec.get("a3"))
    query.bindValue(":a4", rec.get("a4"))
    query.bindValue(":a5", rec.get("a5"))

    if not query.exec():
        logger.error("Failed to insert record: %s", query.lastError().text())
    else:
        logger.info("Record inserted successfully.")

    # Log timestamps
    logger_timestamps("device", rec.get("device_eui"), rec.get("timestamp"))
    logger_timestamps("relay", rec.get("relay_id"), rec.get("relay_ts"))
    logger_timestamps("gateway", rec.get("gateway_id"), rec.get("gateway_ts"))

    return query.lastInsertId()


def export_csv(conn, out_path):
    df = pd.read_sql_query(f"SELECT * FROM {SQLITE_TABLE}", conn)
    df.to_csv(out_path, index=False)
    logger.info("Export CSV done: %s (rows: %d)", out_path, len(df))



# ---- Message handling ----

def extract_fields_from_payload(payload: dict):
    '''Extracts the useful fields of the MQTT request (sent by ChirpStack)
    and those of the decoded datapayload.
    It is assumed that the JSON (excluding the datapayload) contains the following keys
    (careful with the names and cases):
    - `devEui`: **relay** ID
    - `time`: **relay** emission timestamp
    - `gatewayId`: gateway ID
    - `gwTime`: gateway transmission timestamp
    - `fCnt`'''

    # Received elements in the datapayload (decoded by decoder.py)
    print(payload)
    print("data : ", payload.get("data", ""))
    Sensor = decoder.decode_proto_data(payload.get("data", ""))
    device_eui = normalize_eui(Sensor.UI)
    timestamp = Sensor.time
    relay_id = payload.get("deviceInfo").get("devEui")
    relay_ts = payload.get("time")
    gateway_id = payload.get("rxInfo")[0].get("gatewayId")
    gateway_ts = payload.get("rxInfo")[0].get("gwTime")
    fcnt = payload.get("fCnt")

    rec = {
        "device_eui": device_eui,
        "timestamp": timestamp,
        "relay_id": relay_id,
        "relay_ts": relay_ts,
        "gateway_id": gateway_id,
        "gateway_ts": gateway_ts,
        "fcnt": fcnt,
        "a0": Sensor.a0,
        "a1": Sensor.a1,
        "a2": Sensor.a2,
        "a3": Sensor.a3,
        "a4": Sensor.a4,
        "a5": Sensor.a5
    }

    return rec



# ---- MQTT Client and worker ----

class MQTTWorker:
    '''
    Client MQTT with queue for messages and callbacks
    '''
    def __init__(self, broker, port, topic, real_database_insertion=False, ca_cert=None, client_cert=None, client_key=None):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.real_database_insertion = real_database_insertion
        self.ca = ca_cert
        self.cert = client_cert
        self.key = client_key
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.msg_queue = queue.Queue(maxsize=MESSAGE_QUEUE_MAX)
        # attach callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # TLS config if provided
        if self.ca and self.cert and self.key:
            try:
                self.client.tls_set(ca_certs=self.ca, certfile=self.cert, keyfile=self.key)
                logger.info("TLS configuration applied (ca=%s cert=%s key=%s)",
                            self.ca, self.cert, self.key)
            except Exception as e:
                logger.exception("Error in TLS configuration: %s", e)
                raise

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connected to broker %s:%d (rc=%s). Subscription to topic: %s",
                        self.broker, self.port, rc, self.topic)
            client.subscribe(self.topic)
        else:
            logger.error("Error MQTT connexion, rc=%s", rc)
        
    def on_disconnect(self, client, userdata, rc, properties=None):
        logger.warning("Disconnected from broker (rc=%s)", rc)

    def on_message(self, client, userdata, msg):
        # callback in the paho network thread : queue the message for processing
        try:
            payload_bytes = msg.payload
            # decode as utf-8 to JSON
            try:
                payload_text = payload_bytes.decode()
            except Exception:
                # fallback : try latin1
                payload_text = payload_bytes.decode("latin-1", errors="replace")
            self.msg_queue.put_nowait((msg.topic, payload_text))
        except queue.Full:
            logger.warning("Queue is full — message ignored")
        except Exception as e:
            logger.exception("Error on_message: %s", e)

        print(f"[MQTT] Received message on topic '{msg.topic}'")
        print(f"[MQTT] Payload: {payload_text}")

    def connect_and_loop_start(self):
        logger.info("Connecting to MQTT broker %s:%d", self.broker, self.port)
        self.client.connect(self.broker, self.port, keepalive=MQTT_KEEPALIVE)
        # start loop in background thread
        self.client.loop_start()
        '''
        if errors occur, handle them here
        try:
            self.client.connect(self.broker, self.port, keepalive=MQTT_KEEPALIVE)
            # start loop in background thread
            self.client.loop_start()
        except ConnectionResetError as e:
            logger.exception("Connection reset error: %s. Check broker TLS settings/port and broker logs.", e)
            raise
        except ssl.SSLError as e:
            logger.exception("SSL error during connection: %s. Check TLS certificates", e)
            raise
        except Exception as e:
            logger.exception("MQTT connection failed: %s", e)'''

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


def processing_worker(mqtt_worker:MQTTWorker, db_conn, device_euis_normalized):
    '''Processing thread : read queue, parse, filter, insert into DB'''
    while True:
        try:
            topic, payload_text = mqtt_worker.msg_queue.get()
            if payload_text is None:
                continue
            # try JSON parsing of MQTT payload
            try:
                payload_json = json.loads(payload_text)
            except Exception:
                # if it is not JSON, try to store the raw payload
                payload_json = {"_raw_payload_text": payload_text}

            # intelligent extraction of fields
            fields = extract_fields_from_payload(payload_json)

            device_eui = fields["device_eui"]

            if not device_eui:
                logger.debug("Message without device_eui detected on topic %s — Ignored", topic)
                continue

            device_eui = normalize_eui(device_eui)
            # filter by DeviceEUI if exists
            if len(device_euis_normalized) != 0 and device_eui not in device_euis_normalized:
                logger.debug("DeviceEUI %s not in list - Ignored", device_eui)
                continue

            # insert into DB
            try:
                if mqtt_worker.real_database_insertion:
                    rowid = insert_payload(db_conn, fields) # utiliser le fichier annexe real DB
                else:
                    rowid = insert_record(db_conn, fields)
                logger.info("Inserted device=%s ts=%s (%d)", device_eui, rowid,
                            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            except Exception as e:
                logger.exception("Error DB insertion: %s", e)

        except Exception as e:
            logger.exception("Error worker: %s", e)
        finally:
            mqtt_worker.msg_queue.task_done()



# ---- Main ----

def main_mqtt():
    # normalize list of deviceEUIs
    device_euis_normalized = set(normalize_eui(x) for x in DEVICE_EUIS) if DEVICE_EUIS else set()

    # init DB
    conn = init_db(DB_FILENAME)
    logger.info("DB initialized: %s", DB_FILENAME)

    # create mqtt worker
    mqtt_worker = MQTTWorker(
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        topic=MQTT_TOPIC,
        real_database_insertion=REAL_DB_INSERTION,
        ca_cert=MQTT_CA_CERT,
        client_cert=MQTT_CLIENT_CERT,
        client_key=MQTT_CLIENT_KEY
    )

    # start worker thread(s)
    worker_thread = threading.Thread(target=processing_worker,
                                     args=(mqtt_worker, conn, device_euis_normalized),
                                     daemon=True)
    worker_thread.start()

    # connect and loop
    mqtt_worker.connect_and_loop_start()
    logger.info("Worker MQTT started. Ctrl-C to quit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping, MQTT disconnecting...")
    finally:
        mqtt_worker.disconnect()
        conn.close()
        logger.info("Done.")