"""
LoRa Communication Protocol Emulation using MQTT

This module emulates the Arduino LoRa communication protocol used in MOLONARI
sensors and relays, but uses MQTT as the transport layer instead of actual
LoRa radio communication.

The protocol maintains the same packet structure and communication flow:
- 3-way handshake (SYN/SYN-ACK/ACK)
- Data transmission with acknowledgments
- Session closure (FIN)
- Checksum validation
- Retry mechanisms
"""

import json
import time
import threading
import queue as Queue
from enum import IntEnum
from typing import Optional, Dict, Any, List
import logging

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise ImportError("paho-mqtt library is required. Install with: pip install paho-mqtt")


class RequestType(IntEnum):
    """LoRa request types matching Arduino implementation"""
    SYN = 0xcc
    ACK = 0x33
    DATA = 0xc3
    FIN = 0x3c


class LoRaPacket:
    """Represents a LoRa packet with all fields"""
    
    def __init__(self, destination: int, local_address: int, packet_number: int, 
                 request_type: RequestType, payload: str = ""):
        self.destination = destination
        self.local_address = local_address
        self.packet_number = packet_number
        self.request_type = request_type
        self.payload = payload
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> int:
        """Calculate XOR checksum matching Arduino implementation"""
        checksum = self.destination ^ self.local_address ^ self.packet_number ^ int(self.request_type)
        for char in self.payload:
            checksum ^= ord(char)
        return checksum & 0xFF
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary for JSON serialization"""
        return {
            'checksum': self.checksum,
            'destination': self.destination,
            'local_address': self.local_address,
            'packet_number': self.packet_number,
            'request_type': int(self.request_type),
            'payload': self.payload
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoRaPacket':
        """Create packet from dictionary"""
        packet = cls(
            destination=data['destination'],
            local_address=data['local_address'],
            packet_number=data['packet_number'],
            request_type=RequestType(data['request_type']),
            payload=data['payload']
        )
        # Verify checksum
        if packet.checksum != data['checksum']:
            raise ValueError("Checksum mismatch")
        return packet
    
    def to_json(self) -> str:
        """Convert packet to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LoRaPacket':
        """Create packet from JSON string"""
        return cls.from_dict(json.loads(json_str))


class LoRaCommunication:
    """
    Python emulation of Arduino LoRa communication using MQTT transport
    
    This class provides the same interface as the Arduino LoraCommunication class
    but uses MQTT for actual message transport.
    """
    
    def __init__(self, frequency: float, local_address: int, destination: int = 0xff,
                 mqtt_broker: str = "localhost", mqtt_port: int = 1883,
                 debug: bool = False):
        """
        Initialize LoRa communication emulation
        
        Args:
            frequency: LoRa frequency (kept for compatibility, not used in MQTT)
            local_address: Address of this device
            destination: Default destination address (0xff for broadcast)
            mqtt_broker: MQTT broker hostname
            mqtt_port: MQTT broker port
            debug: Enable debug logging
        """
        self.frequency = frequency
        self.local_address = local_address
        self.destination = destination
        self.default_destination = destination
        self.active = False
        
        # MQTT configuration
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self.mqtt_topic_base = f"molonari/lora/{frequency:.0f}MHz"
        
        # Communication state
        self.my_net = {0xaa, 0xbb, 0xcc}  # Authorized addresses
        self.receive_queue = Queue.Queue()
        self.session_active = False
        
        # Logging setup
        self.logger = logging.getLogger(f"LoRa-{local_address:02x}")
        if debug:
            self.logger.setLevel(logging.DEBUG)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
        
        self.logger.debug(f"LoRa emulation initialized: local={local_address:02x}, dest={destination:02x}")
    
    def start_lora(self) -> bool:
        """Initialize MQTT connection (equivalent to LoRa.begin())"""
        if self.active:
            return True
        
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            # Connect with retries
            for retry in range(3):
                try:
                    self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
                    self.mqtt_client.loop_start()
                    
                    # Wait for connection
                    timeout = time.time() + 5.0
                    while not self.active and time.time() < timeout:
                        time.sleep(0.1)
                    
                    if self.active:
                        self.logger.debug("LoRa started (MQTT connected)")
                        return True
                    
                except Exception as e:
                    self.logger.debug(f"LoRa connection failed (attempt {retry + 1}): {e}")
                    time.sleep(1.0)
            
            self.logger.debug("Starting LoRa failed after retries")
            return False
            
        except Exception as e:
            self.logger.debug(f"Failed to start LoRa: {e}")
            return False
    
    def stop_lora(self):
        """Stop MQTT connection (equivalent to LoRa.end())"""
        if self.active and self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.active = False
            self.logger.debug("LoRa stopped")
    
    def set_dest_to_default(self):
        """Reset destination to default"""
        if self.destination != self.default_destination:
            self.destination = self.default_destination
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.active = True
            # Subscribe to messages for this device
            topic = f"{self.mqtt_topic_base}/device/{self.local_address:02x}"
            client.subscribe(topic)
            self.logger.debug(f"Subscribed to {topic}")
        else:
            self.logger.debug(f"MQTT connection failed with code {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message received callback"""
        try:
            packet = LoRaPacket.from_json(msg.payload.decode())
            self.logger.debug(f"Received packet: {packet.to_dict()}")
            self.receive_queue.put(packet)
        except Exception as e:
            self.logger.debug(f"Failed to parse received message: {e}")
    
    def send_packet(self, packet_number: int, request_type: RequestType, payload: str = ""):
        """Send a LoRa packet via MQTT"""
        if not self.active:
            self.logger.debug("LoRa is not active, cannot send packet")
            return
        
        # Add small delay similar to Arduino implementation
        time.sleep(0.1 + (time.time() % 1) * 0.1)  # 100ms + random component
        
        packet = LoRaPacket(
            destination=self.destination,
            local_address=self.local_address,
            packet_number=packet_number,
            request_type=request_type,
            payload=payload
        )
        
        # Publish to destination device topic
        topic = f"{self.mqtt_topic_base}/device/{self.destination:02x}"
        message = packet.to_json()
        
        try:
            self.mqtt_client.publish(topic, message)
            self.logger.debug(f"Packet sent to {self.destination:02x}: {payload}")
        except Exception as e:
            self.logger.debug(f"Failed to send packet: {e}")
    
    def receive_packet(self, timeout: float = 2.0) -> Optional[LoRaPacket]:
        """
        Receive a LoRa packet with timeout
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            LoRaPacket if received, None if timeout
        """
        if not self.active:
            return None
        
        # Small delay for synchronization
        time.sleep(0.08)
        
        try:
            packet = self.receive_queue.get(timeout=timeout)
            
            # Validate destination
            if not self._is_valid_destination(packet.destination, packet.local_address, packet.request_type):
                self.logger.debug("Message is not for this device or is out of session")
                return None
            
            # Log packet details
            self.logger.debug(f"Received from: 0x{packet.local_address:02x}")
            self.logger.debug(f"Sent to: 0x{packet.destination:02x}")
            self.logger.debug(f"Packet Number ID: {packet.packet_number}")
            self.logger.debug(f"Packet request_type: {packet.request_type}")
            self.logger.debug(f"Message: {packet.payload}")
            
            return packet
            
        except Queue.Empty:
            return None
    
    def _is_valid_destination(self, recipient: int, sender: int, request_type: RequestType) -> bool:
        """Validate packet destination matching Arduino logic"""
        if recipient != self.local_address:
            return False
        
        if (self.destination == sender or 
            (request_type == RequestType.SYN and self.destination == 0xff and sender in self.my_net)):
            self.destination = sender
            return True
        
        return False
    
    def is_lora_active(self) -> bool:
        """Check if LoRa is active"""
        return self.active


    def perform_handshake_sensor(self) -> tuple[bool, int]:
        """
        Perform handshake as a sensor (initiator)
        
        Returns:
            (success, shift_value): success status and shift value from relay
        """
        self.send_packet(0, RequestType.SYN, "")
        self.logger.debug("SYN sent, waiting for SYN-ACK...")
        
        retries = 0
        while retries < 6:
            packet = self.receive_packet(timeout=2.0)
            if packet and packet.request_type == RequestType.SYN:
                shift = packet.packet_number
                self.logger.debug("SYN-ACK received, sending final ACK...")
                self.send_packet(packet.packet_number, RequestType.ACK, "")
                time.sleep(1.0)
                return True, shift
            else:
                # Retry with increasing delay
                delay = (retries + 1) * 0.5  # 0.5, 1.0, 1.5, etc.
                time.sleep(delay)
                self.send_packet(0, RequestType.SYN, "")
                retries += 1
        
        self.logger.debug("Handshake failed")
        return False, 0
    
    def perform_handshake_relay(self, shift_back: int = 0) -> bool:
        """
        Perform handshake as a relay (responder)
        
        Args:
            shift_back: Shift value to send back to sensor
            
        Returns:
            bool: Success status
        """
        # Wait for SYN
        while True:
            packet = self.receive_packet(timeout=60.0)  # Long timeout for initial SYN
            if (packet and packet.request_type == RequestType.SYN and 
                packet.packet_number == 0 and self.destination != 0xff):
                # Send SYN-ACK
                self.send_packet(shift_back, RequestType.SYN, "SYN-ACK")
                break
        
        # Wait for ACK with retries
        retries = 0
        self.logger.debug("SYN-ACK sent")
        while retries < 6:
            packet = self.receive_packet(timeout=3.0)
            if packet and packet.request_type == RequestType.ACK:
                self.logger.debug("Handshake complete. Ready to receive data.")
                return True
            else:
                self.logger.debug("No ACK received, retrying...")
                delay = (retries + 1) * 0.5
                time.sleep(delay)
                self.send_packet(shift_back, RequestType.SYN, "SYN-ACK")
                retries += 1
        
        self.logger.debug("Handshake failed")
        self.stop_lora()
        return False
    
    def send_packets(self, send_queue: List[str]) -> int:
        """
        Send multiple data packets with ACK handling (sensor mode)
        
        Args:
            send_queue: List of payload strings to send
            
        Returns:
            int: Last packet number sent
        """
        packet_number = 0
        queue_copy = send_queue.copy()
        
        while queue_copy:
            message = queue_copy[0]  # Get current message but don't remove yet
            self.send_packet(packet_number, RequestType.DATA, message)
            retries = 0
            
            while retries < 6:
                packet = self.receive_packet(timeout=3.0)
                if (packet and packet.request_type == RequestType.ACK and 
                    packet.packet_number == packet_number):
                    self.logger.debug(f"ACK received for packet {packet_number}")
                    queue_copy.pop(0)  # Remove only after ACK
                    packet_number += 1
                    break
                elif packet and packet.request_type == RequestType.FIN:
                    self.logger.debug(f"FIN received for packet {packet_number}")
                    queue_copy.clear()
                    packet_number += 1
                    break
                else:
                    self.logger.debug(f"No ACK received, retrying for packet {packet_number}")
                    delay = (retries + 1) * 0.5
                    time.sleep(delay)
                    self.send_packet(packet_number, RequestType.DATA, message)
                    retries += 1
            
            if retries == 6:
                self.logger.debug(f"Packet send failed after retries for packet {packet_number}")
                queue_copy.clear()
                break
            
            time.sleep(0.1)
        
        return packet_number
    
    def receive_packets(self, receive_queue: List[str], max_queue_size: int = 255) -> int:
        """
        Receive multiple data packets (relay mode)
        
        Args:
            receive_queue: List to store received payloads
            max_queue_size: Maximum queue size
            
        Returns:
            int: Last packet number received
        """
        packet_number = 0
        previous_packet_number = -1
        timeout = 60.0  # 60 second timeout
        
        # Add destination to queue (Arduino behavior)
        receive_queue.append(f"{self.destination:02x}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            packet = self.receive_packet(timeout=5.0)
            if not packet:
                continue
            
            if packet.request_type == RequestType.FIN:
                self.logger.debug("FIN received, session closing")
                return packet.packet_number
            
            if len(receive_queue) >= max_queue_size:
                self.logger.debug("Queue full, sending FIN to close session")
                return packet.packet_number
            
            if previous_packet_number == packet.packet_number:
                # Duplicate packet, just send ACK
                self.send_packet(packet.packet_number, RequestType.ACK, "ACK")
                continue
            
            previous_packet_number = packet.packet_number
            receive_queue.append(packet.payload)
            self.send_packet(packet.packet_number, RequestType.ACK, "ACK")
            self.logger.debug(f"ACK sent for packet {packet.packet_number}")
        
        self.logger.debug(f"Connection lost at packet_number: {packet_number}")
        return packet_number
    
    def close_session(self, last_packet: int):
        """
        Close communication session with FIN handshake
        
        Args:
            last_packet: Number of the last packet in the session
        """
        self.send_packet(last_packet, RequestType.FIN, "")
        self.logger.debug("FIN sent, waiting for final ACK...")
        
        retries = 0
        while retries < 3:
            packet = self.receive_packet(timeout=2.0)
            if (packet and packet.request_type == RequestType.FIN and 
                packet.packet_number == last_packet):
                self.logger.debug("Final ACK received, session closed")
                return
            else:
                self.logger.debug("No final ACK, retrying...")
                delay = (retries + 1) * 0.5
                time.sleep(delay)
                self.send_packet(last_packet, RequestType.FIN, "")
                retries += 1
        
        self.logger.debug("Session closure failed after retries")


class LoRaSensorEmulator(LoRaCommunication):
    """Sensor-specific LoRa emulation with simplified interface"""
    
    def __init__(self, local_address: int, relay_address: int = 0xaa, **kwargs):
        super().__init__(frequency=868e6, local_address=local_address, 
                        destination=relay_address, **kwargs)
        self.relay_address = relay_address
    
    def send_data_session(self, data_list: List[str]) -> bool:
        """
        Complete sensor data transmission session
        
        Args:
            data_list: List of data strings to transmit
            
        Returns:
            bool: Success status
        """
        if not self.start_lora():
            return False
        
        try:
            # Perform handshake
            success, shift = self.perform_handshake_sensor()
            if not success:
                return False
            
            # Send data packets
            last_packet = self.send_packets(data_list)
            
            # Close session
            self.close_session(last_packet)
            
            return True
            
        finally:
            self.stop_lora()


class LoRaRelayEmulator(LoRaCommunication):
    """Relay-specific LoRa emulation with simplified interface"""
    
    def __init__(self, local_address: int = 0xaa, **kwargs):
        super().__init__(frequency=868e6, local_address=local_address, 
                        destination=0xff, **kwargs)  # Broadcast initially
        self.authorized_sensors = {0xbb, 0xcc}  # Default sensor addresses
    
    def receive_data_session(self, shift_back: int = 0) -> Optional[List[str]]:
        """
        Complete relay data reception session
        
        Args:
            shift_back: Shift value to send back in handshake
            
        Returns:
            List[str]: Received data or None if failed
        """
        if not self.start_lora():
            return None
        
        try:
            # Reset destination before starting
            self.set_dest_to_default()
            
            # Perform handshake
            if not self.perform_handshake_relay(shift_back):
                return None
            
            # Receive data packets
            receive_queue = []
            last_packet = self.receive_packets(receive_queue)
            
            # Close session
            self.close_session(last_packet)
            
            return receive_queue
            
        finally:
            self.stop_lora()