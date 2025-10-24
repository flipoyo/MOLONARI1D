from dataclasses import dataclass
import base64
import math
import sensor_pb2
from datetime import datetime, timezone

def int_to_iso8601(value: int) -> str:
    s = f"{value:010d}"  # toujours 10 chiffres
    month = int(s[0:2])
    day = int(s[2:4])
    year = int(s[4:6]) + 2000  # 2000+YY
    hour = int(s[6:8])
    minute = int(s[8:10])

    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return dt.isoformat()

@dataclass
class Sensor:
    UI: str
    time: str
    a0: float
    a1: float
    a2: float
    a3: float
    a4: float

def decode_proto_data(data_b64: str) -> Sensor | None:
    """
    Decode un payload base64 contenant un message Protobuf SensorData.
    Retourne un objet Sensor (avec NaN si certaines valeurs manquent).
    """
    try:
        # Décodage base64 -> bytes
        data_bytes = base64.b64decode(data_b64)
        
        # Désérialisation protobuf
        msg = sensor_pb2.SensorData()
        msg.ParseFromString(data_bytes)
        
        # On récupère les valeurs, en complétant avec NaN
        measurements = list(msg.measurements)
        while len(measurements) < 5:
            measurements.append(float('nan'))
        
        return Sensor(
            UI = msg.UI,
            time = int_to_iso8601(msg.time),
            a0=measurements[0],
            a1=measurements[1],
            a2=measurements[2],
            a3=measurements[3],
            a4=measurements[4]
        )
    except Exception as e:
        print("Erreur décodage Protobuf:", e)
        return None

data_b64 = "CgtmZXJoZnVpZXJpdRCjrbPoAxoUZmZmPwrX4z+F6zFAmpl5QFyPL0I="
print(decode_proto_data(data_b64))

