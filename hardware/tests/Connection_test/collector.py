#!/usr/bin/env python3
"""
collector_minimal.py
Micro-service MQTT -> SQLite (stockage brut des uplinks)
Usage: python3 collector_minimal.py
"""

import sqlite3
import json
import time
import paho.mqtt.client as mqtt


# --- Configuration MQTT ---
BROKER = "terra-forma-obs.fr"
PORT = 10088
TOPIC_SUB = "application/+/device/+/event/up"

DB_FILENAME = "uplinks_raw.db"

# --- DB init ---
def init_db(db_filename=DB_FILENAME):
conn = sqlite3.connect(db_filename, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS uplinks (
id INTEGER PRIMARY KEY AUTOINCREMENT,
topic TEXT,
payload TEXT,
received_at TEXT
)
""")
conn.commit()
print(f"[DB] Initialized or found existing DB '{db_filename}'")
return conn

# --- MQTT callbacks ---
def on_connect(client, userdata, flags, rc):
print(f"[MQTT] Connected to broker, rc={rc}")
client.subscribe(TOPIC_SUB, qos=1)
print(f"[MQTT] Subscribed to topic '{TOPIC_SUB}'")

def on_message(client, userdata, msg):
conn = userdata["db_conn"]
payload_text = msg.payload.decode()
received_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

print(f"[MQTT] Received message on topic '{msg.topic}'")
print(f"[MQTT] Payload: {payload_text}")

c = conn.cursor()
try:
c.execute(
"INSERT INTO uplinks (topic, payload, received_at) VALUES (?,?,?)",
(msg.topic, payload_text, received_time)
)
conn.commit()
print(f"[DB] Inserted message into DB at {received_time}")
except Exception as e:
print(f"[DB] Error inserting into DB: {e}")

# --- Main ---
def main():
conn = init_db(DB_FILENAME)
client = mqtt.Client(client_id="collector_minimal", userdata={"db_conn": conn})
client.on_connect = on_connect
client.on_message = on_message

# TLS si nécessaire
client.tls_set(
ca_certs="./ca_mqtt.pem",
certfile="./tls_mqtt.pem",
keyfile="./key_mqtt.pem"
)
client.tls_insecure_set(False)

print(f"[MQTT] Connecting to broker {BROKER}:{PORT}...")
client.connect(BROKER, PORT, 60)
client.loop_forever()

if __name__ == "__main__":
main()
