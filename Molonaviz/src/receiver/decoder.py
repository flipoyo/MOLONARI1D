from dataclasses import dataclass
import base64
from . import sensor_pb2
from datetime import datetime, timezone

NB_MEASUREMENTS = 6

def int_to_iso8601(value: int) -> str:
    s = f"{value:010d}"  # always 10 digits
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
    a5: float

def decode_proto_data(data_b64: str) -> Sensor | None:
    """
    Decodes a base64 payload containing a Protobuf SensorData message.
    Returns a Sensor object (with NaN if some values are missing).
    """
    try:
        # Decoding base64 to bytes
        data_bytes = base64.b64decode(data_b64)
        
        # Protobuf deserialization
        msg = sensor_pb2.SensorData()
        msg.ParseFromString(data_bytes)
        
        # Value extraction with NaN for missing measurements
        measurements = list(msg.measurements)
        while len(measurements) < NB_MEASUREMENTS:
            measurements.append(float('nan'))
        
        return Sensor(
            UI = msg.UI,
            time = int_to_iso8601(msg.time),
            a0=measurements[0],
            a1=measurements[1],
            a2=measurements[2],
            a3=measurements[3],
            a4=measurements[4],
            a5=measurements[5]
        )
    except Exception as e:
        print("Error in Protobuf decoding:", e)
        return None