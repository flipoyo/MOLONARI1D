#!/usr/bin/env python3
"""
adapt_nodered_mqtt.py

Objectives :
- Get MQTT TLS connection (cert/key/ca) on a broker (10088 port for ChirpStack)
- Filter messages by DeviceEUI
- Extract fields of interest and insert them in a SQLite DB

"""

import json
import queue
import threading
import time

import paho.mqtt.client as mqtt

from . import decoder
from .db_insertion import init_db, insert_record
from ..molonaviz.backend.DatabaseManager import DatabaseManager


def normalize_eui(eui):
    '''Normalizes a DeviceEUI in lowercase without spaces. Returns None if input is None.'''
    if eui is None:
        return None
    return str(eui).strip().lower()



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
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
        self.broker = config["mqtt"]["broker"]
        self.port = config["mqtt"]["port"]
        self.topic = config["mqtt"]["topic"]
        self.ca = config["mqtt"]["ca_cert"]
        self.cert = config["mqtt"]["client_cert"]
        self.key = config["mqtt"]["client_key"]
        self.client = mqtt.Client(client_id=config["mqtt"]["client_id"])
        self.msg_queue = queue.Queue(maxsize=config["mqtt"]["message_queue_max"])
        self.keepalive = config["mqtt"]["keepalive"]
        
        self.real_database_insertion = config["database"]["real_database_insertion"]
        
        if self.real_database_insertion:
            self.db_manager = DatabaseManager(config["database"]["filename"],
                                              config["database"]["ERD_structure"])
        else:
            self.db_manager = init_db(logger, config["database"]["filename"])

        # attach callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # TLS config if provided
        try:
            self.client.tls_set(ca_certs=self.ca, certfile=self.cert, keyfile=self.key)
            logger.info("TLS configuration applied (ca=%s cert=%s key=%s)",
                        self.ca, self.cert, self.key)
        except Exception as e:
            logger.exception("Error in TLS configuration: %s", e)
            raise

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.logger.info("Connected to broker %s:%d (rc=%s). Subscription to topic: %s",
                        self.broker, self.port, rc, self.topic)
            client.subscribe(self.topic)
        else:
            self.logger.error("Error MQTT connexion, rc=%s", rc)

    def on_disconnect(self, client, userdata, rc, properties=None):
        self.logger.warning("Disconnected from broker (rc=%s)", rc)

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
            self.logger.warning("Queue is full — message ignored")
        except Exception as e:
            self.logger.exception("Error on_message: %s", e)

        self.logger.info("Received message on topic '%s'", msg.topic)

    def connect_and_loop_start(self):
        self.logger.info("Connecting to MQTT broker %s:%d", self.broker, self.port)
        self.client.connect(self.broker, self.port, keepalive=self.keepalive)
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


def processing_worker(logger, mqtt_worker:MQTTWorker, device_euis_normalized):
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
                if mqtt_worker.real_database_insertion and mqtt_worker.db_manager:
                    mqtt_worker.db_manager.insert_payload(fields)
                else:
                    insert_record(logger, mqtt_worker.db_manager, fields)
                logger.info("Inserted device=%s, at ts=%s", device_eui, \
                            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            except Exception as e:
                logger.exception("Error DB insertion: %s", e)

        except Exception as e:
            logger.exception("Error worker: %s", e)
        finally:
            mqtt_worker.msg_queue.task_done()


# ---- Main ----

def main_mqtt(config, logger):
    # normalize list of deviceEUIs
    device_euis_normalized = set(normalize_eui(x) for x in config["mqtt"]["device_euis"]) if config["mqtt"]["device_euis"] else set()

    # init DB
    mqtt_worker = MQTTWorker(config, logger)

    logger.info("DB initialized: %s", config["database"]["filename"])

    # start worker thread(s)
    worker_thread = threading.Thread(target=processing_worker,
                                     args=(logger, mqtt_worker, device_euis_normalized),
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
        if mqtt_worker.db_manager and not mqtt_worker.real_database_insertion:
            mqtt_worker.db_manager.close()
        else:
            mqtt_worker.db_manager.close()
        logger.info("Done.")