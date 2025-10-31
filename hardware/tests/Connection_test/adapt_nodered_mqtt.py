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

import argparse
import base64
import json
import logging
import queue
import sqlite3
import sys
import threading
import time
import os
from datetime import datetime

import pandas as pd
import paho.mqtt.client as mqtt



# ---- MQTT configuration ----

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "devices/{dev_eui}/up"
MQTT_CLIENT_ID = "emulator-poc"
MQTT_KEEPALIVE = 60

# paths to TLS files
MQTT_CA_CERT = "/TLS/ca.crt"
MQTT_CLIENT_CERT = "/TLS/client.crt"
MQTT_CLIENT_KEY = "/TLS/client.key"

# SQLite DB configuration
DB_FILENAME = "measurements.db"
SQLITE_TABLE = "uplinks"

DEVICE_EUIS = [
    # list of deviceEUIs to collect
]

# Queue size for incoming messages (to not block the MQTT callback)
MESSAGE_QUEUE_MAX = 1000

# Logging to better control infos and alerts displayed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("chirpstack")



# ---- Utilitary functions ----

def normalize_eui(eui):
    '''Normalizes a DeviceEUI in lowercase without spaces. Returns None if input is None.'''
    if eui is None:
        return None
    return str(eui).strip().lower()

### voir fonction decode de Gabriel
"""
def decode_base64_to_text(b64str):
    '''Décode une chaîne base64 en texte UTF-8. Retourne texte ou None.'''
    if not b64str or not isinstance(b64str, str):
        return None
    try:
        b = base64.b64decode(b64str, validate=False)
        return b.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Erreur décodage base64: %s", e)
        return None

def try_parse_json(text):
    '''Tente de parser du JSON ; remplace NaN par null. Retourne un objet ou None.'''
    if text is None:
        return None
    txt = text.strip()
    if not txt:
        return None
    # heuristique : n'essayer de parser que si commence par { ou [
    if not (txt.startswith("{") or txt.startswith("[")):
        return None
    # remplace NaN/NaN-like par null pour éviter JSON.parse errors
    cleaned = txt.replace("NaN", "null").replace("nan", "null")
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.debug("JSON parse error (ignored): %s", e)
        return None
"""


# ---- Database setup ----

def init_db(db_path=DB_FILENAME):
    '''Initializes the SQLite DB and creates the table if necessary. Returns the connexion.'''
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(f'''
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
        a4 REAL
    )
    ''')
    conn.commit()
    logger.info("Table '%s' initialized in DB '%s'", SQLITE_TABLE, db_path)
    return conn
    
from logger_timestamps import get_logger

def insert_record(conn, rec):
    '''ATTENTION: *`rec`* should be a dict with keys:
      `device_eui`, `timestamp`, `relay_id`, `relay_ts`, `gateway_id`, `gateway_ts`,
      `fcnt`, `a0`, `a1`, `a2`, `a3`, `a4`'''
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {SQLITE_TABLE} (
            device_eui, timestamp, relay_id, gateway_id, fcnt, a0, a1, a2, a3, a4
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rec.get("device_eui"),
        rec.get("timestamp"),
        rec.get("relay_id"),
        rec.get("gateway_id"),
        rec.get("fcnt"),
        rec.get("a0"),
        rec.get("a1"),
        rec.get("a2"),
        rec.get("a3"),
        rec.get("a4")
    ))
    conn.commit()

    # Log timestamps
    get_logger("device", rec.get("device_eui"), rec.get("timestamp"))
    get_logger("relay", rec.get("relay_id"), rec.get("relay_ts"))
    get_logger("gateway", rec.get("gateway_id"), rec.get("gateway_ts"))

    return cur.lastrowid # Returns the inserted row ID


def export_csv(conn, out_path):
    df = pd.read_sql_query(f"SELECT * FROM {SQLITE_TABLE}", conn)
    df.to_csv(out_path, index=False)
    logger.info("Export CSV done: %s (rows: %d)", out_path, len(df))



# ---- Message handling ----

import decoder # assuming decoder.py is in the same directory

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
    Sensor = decoder.decode_proto_data(payload.get("data", ""))
    device_eui = normalize_eui(Sensor.UI)
    timestamp = Sensor.time
    a0 = Sensor.a0
    a1 = Sensor.a1
    a2 = Sensor.a2
    a3 = Sensor.a3
    a4 = Sensor.a4
    relay_id = payload.get("devEui")
    relay_ts = payload.get("time")
    gateway_id = payload.get("gatewayId")
    gateway_ts = payload.get("gwTime")
    fcnt = payload.get("fCnt")

    rec = {
        "device_eui": device_eui,
        "timestamp": timestamp,
        "relay_id": relay_id,
        "relay_ts": relay_ts,
        "gateway_id": gateway_id,
        "gateway_ts": gateway_ts,
        "fcnt": fcnt,
        "a0": a0,
        "a1": a1,
        "a2": a2,
        "a3": a3, 
        "a4": a4
    }

    return rec



# ---- MQTT Client and worker ----

class MQTTWorker:
    '''Client MQTT with queue for messages and callbacks
    Goal: free the worker from NodeRED'''
    def __init__(self, broker, port, topic, ca_cert=None, client_cert=None, client_key=None):
        self.broker = broker
        self.port = port
        self.topic = topic
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
            if not (os.path.exists(self.ca) and os.path.exists(self.cert) and os.path.exists(self.key)):
                logger.error("TLS files not found: ca=%s cert=%s key=%s. Skipping TLS setup.",
                             self.ca, self.cert, self.key)
            else:
                try:
                    self.client.tls_set(ca_certs=self.ca, certfile=self.cert, keyfile=self.key)
                    logger.info("TLS configuration applied (ca=%s cert=%s key=%s)",
                                self.ca, self.cert, self.key)
                except Exception as e:
                    logger.exception("Error in TLS configuration: %s", e)
                    raise

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to broker %s:%d (rc=%s). Subscription to topic: %s",
                        self.broker, self.port, rc, self.topic)
            client.subscribe(self.topic)
        else:
            logger.error("Error MQTT connexion, rc=%s", rc)
        
    def on_disconnect(self, client, userdata, rc):
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
        self.client.connect(self.broker, self.port, keepalive=MQTT_KEEPALIVE)
        # start loop in background thread
        self.client.loop_start()

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
            if device_euis_normalized and device_eui not in device_euis_normalized:
                logger.debug("DeviceEUI %s not in list - Ignored", device_eui)
                continue

            # insert into DB
            try:
                rowid = insert_record(db_conn, fields)
                logger.info("Inserted id=%d device=%s ts=%s", rowid, device_eui,
                            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            except Exception as e:
                logger.exception("Error DB insertion: %s", e)

        except Exception as e:
            logger.exception("Error worker: %s", e)
        finally:
            mqtt_worker.msg_queue.task_done()



# ---- Main ----

def main(args):
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", help="Export the DB into CSV and quit (file path)", default=None)
    args = parser.parse_args()

    # If export CSV requested, open the DB, export then exit
    if args.export:
        db_conn = init_db(DB_FILENAME)
        export_csv(db_conn, args.export)
        db_conn.close()
        sys.exit(0)

    main(args)