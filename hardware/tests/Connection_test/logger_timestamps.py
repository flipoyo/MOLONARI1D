# Here, we generate a log in which timestamps from the device, the relay and the gateway are stored
# We log the timestamps in the adapt_nodered_mqtt.py file when inserting into the database

import logging
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "timestamps.log")

logger = logging.getLogger("timestamps_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Handler basique pour écrire dans un fichier
    file_handler = logging.FileHandler(LOG_PATH)
    formatter = logging.Formatter('%(asctime)s | %(message)s', '%Y-%m-%dT%H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def get_logger(obj: str, obj_id: str, timestamp):
    '''
    Logs the timestamps from either a device, relay or gateway into timestamps.log` file.
    Args:
        `obj`: 'device', 'relay' or 'gateway'
        `obj_id`: the identifier of the object (e.g., device EUI, relay ID, gateway ID)
        `timestamp`: the timestamp to log
    Returns:
        `None` (just logs the information in the log file)
    '''
    # Vérification de l'objet
    if obj not in ['device', 'relay', 'gateway']:
        raise ValueError("obj must be 'device', 'relay' or 'gateway'")
    
    # Format d'affichage
    if obj == 'device':
        log_message = f"DEVICE: DeviceEUI: {obj_id} | sent at: {timestamp}"
    elif obj == 'relay':
        log_message = f"RELAY: RelayID: {obj_id} | received and trasnmitted at: {timestamp}"
    else:
        log_message = f"GATEWAY: GatewayID: {obj_id} | transmitted at: {timestamp}"
    
    logger.info(log_message)
    return None