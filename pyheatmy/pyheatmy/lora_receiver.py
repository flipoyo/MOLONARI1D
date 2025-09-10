"""
LoRa and LoRaWAN receiver simulation for MOLONARI1D sensor data.

This module provides classes to simulate LoRa and LoRaWAN reception behavior
for sensor data. It receives packets from LoRa emitters, adds receiving timestamps,
and forwards the updated data via LoRaWAN to gateways with optional MQTT integration.
"""

import pandas as pd
import numpy as np
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import random
import queue
import threading
from pathlib import Path

from .lora_emitter import (
    LoRaPacket, LoRaEmitter, LoRaWANEmitter,
    LoRaSpreadingFactor, LoRaFrequency
)

# Optional MQTT support
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    mqtt = None


@dataclass
class ReceivedPacket:
    """Represents a received LoRa packet with additional metadata."""
    original_packet: LoRaPacket
    received_timestamp: datetime
    rssi: float = -80.0  # Received Signal Strength Indicator in dBm
    snr: float = 10.0    # Signal-to-Noise Ratio in dB
    reception_count: int = 1
    reception_success: bool = True


class LoRaReceiver:
    """
    Simulates a LoRa device receiving sensor data and forwarding to gateways.
    
    This class emulates the behavior of Arduino MKR WAN 1310 devices used as
    relays in the MOLONARI1D project, receiving data from sensors and forwarding
    to LoRaWAN gateways.
    """

    def __init__(
        self,
        device_address: int,
        spreading_factor: LoRaSpreadingFactor = LoRaSpreadingFactor.SF7,
        frequency: LoRaFrequency = LoRaFrequency.EU868,
        power: int = 14,  # dBm
        max_queue_size: int = 100,
        reception_success_rate: float = 0.95,
        ack_timeout: float = 5.0,  # seconds
        verbose: bool = False
    ):
        """
        Initialize LoRa receiver.
        
        Parameters:
        -----------
        device_address : int
            Unique address for this receiver device (0-255)
        spreading_factor : LoRaSpreadingFactor
            LoRa spreading factor for reception
        frequency : LoRaFrequency  
            Reception frequency band
        power : int
            Transmission power for acknowledgments in dBm (2-20)
        max_queue_size : int
            Maximum number of packets to queue
        reception_success_rate : float
            Probability of successful packet reception (0.0-1.0)
        ack_timeout : float
            Timeout for acknowledgment transmission in seconds
        verbose : bool
            Enable verbose logging
        """
        self.device_address = device_address
        self.spreading_factor = spreading_factor
        self.frequency = frequency
        self.power = power
        self.max_queue_size = max_queue_size
        self.reception_success_rate = reception_success_rate
        self.ack_timeout = ack_timeout
        self.verbose = verbose
        
        # Reception tracking
        self.received_packets = []
        self.receive_queue = queue.Queue(maxsize=max_queue_size)
        self.is_listening = False
        self.listen_thread = None
        
        # Statistics
        self.total_received = 0
        self.total_forwarded = 0
        self.reception_errors = 0
        
        # Setup logging
        self.logger = logging.getLogger(f"LoRaReceiver_{device_address}")
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def simulate_packet_reception(self, transmitted_packet: Dict[str, Any]) -> Optional[ReceivedPacket]:
        """
        Simulate reception of a transmitted packet.
        
        Parameters:
        -----------
        transmitted_packet : Dict[str, Any]
            Transmission result from LoRaEmitter.simulate_transmission()
            
        Returns:
        --------
        Optional[ReceivedPacket]
            Received packet if reception successful, None otherwise
        """
        if not transmitted_packet.get('success', False):
            # Can't receive a packet that wasn't successfully transmitted
            return None
            
        # Simulate reception success based on various factors
        packet = transmitted_packet['packet']
        
        # Base reception rate
        base_rate = self.reception_success_rate
        
        # Spreading factor affects reception reliability
        sf_bonus = (self.spreading_factor.sf - 7) * 0.01
        
        # Simulate distance/path loss effects
        rssi = -80.0 + random.gauss(0, 10)  # Random RSSI around -80 dBm
        snr = 10.0 + random.gauss(0, 3)    # Random SNR around 10 dB
        
        # Poor signal affects reception
        signal_penalty = 0
        if rssi < -100:
            signal_penalty = 0.2
        elif rssi < -90:
            signal_penalty = 0.1
            
        reception_rate = min(0.99, base_rate + sf_bonus - signal_penalty)
        reception_success = random.random() < reception_rate
        
        if reception_success:
            received_packet = ReceivedPacket(
                original_packet=packet,
                received_timestamp=datetime.now(),
                rssi=rssi,
                snr=snr,
                reception_success=True
            )
            
            self.total_received += 1
            self.received_packets.append(received_packet)
            
            # Add to processing queue if space available
            try:
                self.receive_queue.put_nowait(received_packet)
                self.logger.debug(f"Received packet {packet.packet_number} from device "
                                f"{packet.local_address} (RSSI: {rssi:.1f}dBm, SNR: {snr:.1f}dB)")
            except queue.Full:
                self.logger.warning(f"Receive queue full, dropping packet {packet.packet_number}")
                self.reception_errors += 1
                
            return received_packet
        else:
            self.reception_errors += 1
            self.logger.debug(f"Packet {packet.packet_number} reception failed "
                            f"(RSSI: {rssi:.1f}dBm, SNR: {snr:.1f}dB)")
            return None

    def send_acknowledgment(self, received_packet: ReceivedPacket) -> bool:
        """
        Send acknowledgment back to the transmitter.
        
        Parameters:
        -----------
        received_packet : ReceivedPacket
            The packet to acknowledge
            
        Returns:
        --------
        bool
            True if acknowledgment sent successfully
        """
        original = received_packet.original_packet
        
        # Create ACK packet
        ack_packet = LoRaPacket(
            checksum=0,
            destination=original.local_address,  # Send back to sender
            local_address=self.device_address,
            packet_number=original.packet_number,
            request_type=0xAC,  # ACK request type
            payload=f"ACK:{original.packet_number}",
            timestamp=datetime.now()
        )
        ack_packet.checksum = ack_packet.calculate_checksum()
        
        # Simulate ACK transmission delay and potential failure
        time.sleep(0.1)  # Small ACK delay
        ack_success = random.random() < 0.95  # 95% ACK success rate
        
        if ack_success:
            self.logger.debug(f"Sent ACK for packet {original.packet_number} to device {original.local_address}")
            return True
        else:
            self.logger.warning(f"ACK transmission failed for packet {original.packet_number}")
            return False

    def add_reception_timestamp(self, received_packet: ReceivedPacket) -> str:
        """
        Add reception timestamp to the packet payload.
        
        Parameters:
        -----------
        received_packet : ReceivedPacket
            The received packet to process
            
        Returns:
        --------
        str
            Updated payload with reception timestamp
        """
        original_payload = received_packet.original_packet.payload
        reception_time = received_packet.received_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Add reception timestamp to payload
        # Format: "original_payload,RX_TIME:2024-11-07 10:00:12.123"
        updated_payload = f"{original_payload},RX_TIME:{reception_time}"
        
        return updated_payload

    def process_received_packets(self, 
                               packet_processor: Callable[[ReceivedPacket], bool] = None,
                               send_acks: bool = True) -> List[ReceivedPacket]:
        """
        Process packets from the receive queue.
        
        Parameters:
        -----------
        packet_processor : Callable, optional
            Function to process each received packet
        send_acks : bool
            Whether to send acknowledgments
            
        Returns:
        --------
        List[ReceivedPacket]
            List of processed packets
        """
        processed_packets = []
        
        while not self.receive_queue.empty():
            try:
                received_packet = self.receive_queue.get_nowait()
                
                # Send acknowledgment if requested
                if send_acks:
                    self.send_acknowledgment(received_packet)
                
                # Process with custom processor if provided
                if packet_processor:
                    try:
                        success = packet_processor(received_packet)
                        if not success:
                            self.logger.warning(f"Packet processor failed for packet {received_packet.original_packet.packet_number}")
                    except Exception as e:
                        self.logger.error(f"Error in packet processor: {e}")
                
                processed_packets.append(received_packet)
                
            except queue.Empty:
                break
                
        return processed_packets

    def save_received_data_to_csv(self, csv_path: str, append: bool = True) -> int:
        """
        Save received packet data to CSV file.
        
        Parameters:
        -----------
        csv_path : str
            Path to output CSV file
        append : bool
            Whether to append to existing file
            
        Returns:
        --------
        int
            Number of packets saved
        """
        if not self.received_packets:
            self.logger.warning("No received packets to save")
            return 0
            
        # Convert received packets to DataFrame
        data_rows = []
        for rp in self.received_packets:
            # Parse original payload
            payload = rp.original_packet.payload
            payload_parts = payload.split(',')
            
            # Create row with original data plus reception metadata
            row = {
                'sender_address': rp.original_packet.local_address,
                'packet_number': rp.original_packet.packet_number,
                'original_timestamp': rp.original_packet.timestamp.isoformat(),
                'received_timestamp': rp.received_timestamp.isoformat(),
                'rssi_dbm': rp.rssi,
                'snr_db': rp.snr,
                'original_payload': payload
            }
            
            # Add payload data as individual columns if it looks like sensor data
            try:
                # Assuming payload format: "date,time,temp1,temp2,temp3,temp4,pressure"
                if len(payload_parts) >= 5:
                    row.update({
                        'payload_date': payload_parts[0] if len(payload_parts) > 0 else '',
                        'payload_time': payload_parts[1] if len(payload_parts) > 1 else '',
                        'temp_1': float(payload_parts[2]) if len(payload_parts) > 2 else None,
                        'temp_2': float(payload_parts[3]) if len(payload_parts) > 3 else None,
                        'temp_3': float(payload_parts[4]) if len(payload_parts) > 4 else None,
                        'temp_4': float(payload_parts[5]) if len(payload_parts) > 5 else None,
                        'pressure': float(payload_parts[6]) if len(payload_parts) > 6 else None,
                    })
            except (ValueError, IndexError):
                # If payload doesn't match expected format, just save as-is
                pass
                
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Save to CSV
        mode = 'a' if append and Path(csv_path).exists() else 'w'
        header = not (append and Path(csv_path).exists())
        
        df.to_csv(csv_path, mode=mode, header=header, index=False)
        
        self.logger.info(f"Saved {len(data_rows)} received packets to {csv_path}")
        return len(data_rows)

    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed reception statistics."""
        total_attempted = self.total_received + self.reception_errors
        reception_rate = self.total_received / total_attempted if total_attempted > 0 else 0.0
        
        return {
            'device_address': self.device_address,
            'total_received': self.total_received,
            'total_forwarded': self.total_forwarded,
            'reception_errors': self.reception_errors,
            'reception_rate': reception_rate,
            'queue_size': self.receive_queue.qsize(),
            'packets_in_memory': len(self.received_packets),
            'spreading_factor': self.spreading_factor.sf,
            'frequency_mhz': self.frequency.value,
            'power_dbm': self.power
        }


class LoRaWANReceiver(LoRaReceiver):
    """
    Extends LoRaReceiver to forward received data via LoRaWAN to gateways.
    
    Acts as a relay device that receives LoRa packets and forwards them
    to LoRaWAN networks, adding reception timestamps and metadata.
    """

    def __init__(
        self,
        device_address: int,
        app_eui: str = "0000000000000000",
        app_key: str = "387BC5DEF778168781DDE361D4407953",
        duty_cycle_limit: float = 0.01,  # 1% duty cycle limit
        join_retry_interval: float = 60.0,  # seconds
        mqtt_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize LoRaWAN receiver with relay capabilities.
        
        Parameters:
        -----------
        device_address : int
            Device address for receiver
        app_eui : str
            Application EUI for OTAA
        app_key : str
            Application key for OTAA
        duty_cycle_limit : float
            Maximum duty cycle for LoRaWAN transmission
        join_retry_interval : float
            Interval between join attempts
        mqtt_config : dict, optional
            MQTT broker configuration {'broker': 'host', 'port': 1883, 'topic': 'molonari/data'}
        **kwargs
            Additional arguments passed to LoRaReceiver
        """
        super().__init__(device_address, **kwargs)
        
        # LoRaWAN emitter for forwarding
        self.lorawan_emitter = LoRaWANEmitter(
            device_address=device_address,
            app_eui=app_eui,
            app_key=app_key,
            duty_cycle_limit=duty_cycle_limit,
            join_retry_interval=join_retry_interval,
            spreading_factor=self.spreading_factor,
            frequency=self.frequency,
            power=self.power,
            verbose=self.verbose
        )
        
        # MQTT configuration
        self.mqtt_config = mqtt_config or {}
        self.mqtt_client = None
        self.mqtt_connected = False
        
        if MQTT_AVAILABLE and self.mqtt_config:
            self._setup_mqtt()

    def _setup_mqtt(self):
        """Setup MQTT client if configuration provided."""
        if not MQTT_AVAILABLE:
            self.logger.warning("MQTT support not available - install paho-mqtt")
            return
            
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            
            # Connect to broker
            broker = self.mqtt_config.get('broker', 'localhost')
            port = self.mqtt_config.get('port', 1883)
            
            self.mqtt_client.connect(broker, port, 60)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            self.logger.error(f"Failed to setup MQTT: {e}")

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.mqtt_connected = True
            self.logger.info("Connected to MQTT broker")
        else:
            self.logger.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        self.mqtt_connected = False
        self.logger.warning("Disconnected from MQTT broker")

    def join_lorawan_network(self, max_attempts: int = 5) -> bool:
        """Join the LoRaWAN network for forwarding."""
        return self.lorawan_emitter.join_network(max_attempts)

    def forward_via_lorawan(self, received_packet: ReceivedPacket) -> Dict[str, Any]:
        """
        Forward received packet via LoRaWAN with added metadata.
        
        Parameters:
        -----------
        received_packet : ReceivedPacket
            The packet to forward
            
        Returns:
        --------
        Dict[str, Any]
            Forwarding result
        """
        # Add reception timestamp to payload
        updated_payload = self.add_reception_timestamp(received_packet)
        
        # Create new packet for LoRaWAN transmission
        relay_packet = LoRaPacket(
            checksum=0,
            destination=0x00,  # Gateway
            local_address=self.device_address,
            packet_number=self.lorawan_emitter.packet_counter % 256,
            request_type=0xC4,  # Relay data transfer
            payload=updated_payload,
            timestamp=datetime.now()
        )
        relay_packet.checksum = relay_packet.calculate_checksum()
        
        # Forward via LoRaWAN
        result = self.lorawan_emitter.simulate_transmission(relay_packet)
        
        if result.get('success', False):
            self.total_forwarded += 1
            self.logger.debug(f"Forwarded packet {received_packet.original_packet.packet_number} "
                            f"via LoRaWAN (DevAddr: {self.lorawan_emitter.dev_addr})")
        else:
            self.logger.warning(f"Failed to forward packet {received_packet.original_packet.packet_number} "
                              f"via LoRaWAN: {result.get('error', 'unknown')}")
        
        return result

    def publish_to_mqtt(self, received_packet: ReceivedPacket) -> bool:
        """
        Publish received packet data to MQTT broker.
        
        Parameters:
        -----------
        received_packet : ReceivedPacket
            The packet to publish
            
        Returns:
        --------
        bool
            True if published successfully
        """
        if not self.mqtt_connected or not self.mqtt_client:
            return False
            
        try:
            # Create MQTT payload
            mqtt_payload = {
                'device_id': f'molonari_{received_packet.original_packet.local_address:02X}',
                'packet_number': received_packet.original_packet.packet_number,
                'original_timestamp': received_packet.original_packet.timestamp.isoformat(),
                'received_timestamp': received_packet.received_timestamp.isoformat(),
                'relay_address': self.device_address,
                'rssi': received_packet.rssi,
                'snr': received_packet.snr,
                'data': received_packet.original_packet.payload
            }
            
            # Parse sensor data if possible
            payload_parts = received_packet.original_packet.payload.split(',')
            if len(payload_parts) >= 5:
                try:
                    mqtt_payload['sensor_data'] = {
                        'date': payload_parts[0],
                        'time': payload_parts[1],
                        'temperatures': [float(x) for x in payload_parts[2:6] if x],
                        'pressure': float(payload_parts[6]) if len(payload_parts) > 6 else None
                    }
                except (ValueError, IndexError):
                    pass
            
            # Publish to MQTT
            topic = self.mqtt_config.get('topic', 'molonari/data')
            payload_json = json.dumps(mqtt_payload, default=str)
            
            result = self.mqtt_client.publish(topic, payload_json)
            
            if result.rc == 0:
                self.logger.debug(f"Published packet {received_packet.original_packet.packet_number} to MQTT topic {topic}")
                return True
            else:
                self.logger.warning(f"Failed to publish to MQTT: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing to MQTT: {e}")
            return False

    def relay_packet_processor(self, received_packet: ReceivedPacket) -> bool:
        """
        Process received packet as a relay (forward via LoRaWAN and MQTT).
        
        Parameters:
        -----------
        received_packet : ReceivedPacket
            The packet to process
            
        Returns:
        --------
        bool
            True if processing successful
        """
        success = True
        
        # Forward via LoRaWAN if joined
        if self.lorawan_emitter.is_joined:
            lorawan_result = self.forward_via_lorawan(received_packet)
            if not lorawan_result.get('success', False):
                success = False
        else:
            self.logger.warning("Cannot forward via LoRaWAN - not joined to network")
            success = False
        
        # Publish to MQTT if configured
        if self.mqtt_config:
            mqtt_success = self.publish_to_mqtt(received_packet)
            if not mqtt_success:
                success = False
        
        return success

    def start_relay_operation(self, auto_process: bool = True, 
                             process_interval: float = 1.0) -> bool:
        """
        Start relay operation (join LoRaWAN and begin processing).
        
        Parameters:
        -----------
        auto_process : bool
            Whether to automatically process received packets
        process_interval : float
            Interval between processing cycles in seconds
            
        Returns:
        --------
        bool
            True if relay started successfully
        """
        # Join LoRaWAN network
        if not self.lorawan_emitter.is_joined:
            self.logger.info("Joining LoRaWAN network for relay operation...")
            if not self.join_lorawan_network():
                self.logger.error("Failed to join LoRaWAN network - relay operation limited")
                return False
        
        self.logger.info(f"Relay operation started (DevAddr: {self.lorawan_emitter.dev_addr})")
        
        if auto_process:
            # Start automatic processing in background
            def auto_process_loop():
                while self.is_listening:
                    processed = self.process_received_packets(
                        packet_processor=self.relay_packet_processor,
                        send_acks=True
                    )
                    if processed:
                        self.logger.debug(f"Auto-processed {len(processed)} packets")
                    time.sleep(process_interval)
                    
            self.is_listening = True
            self.listen_thread = threading.Thread(target=auto_process_loop, daemon=True)
            self.listen_thread.start()
        
        return True

    def stop_relay_operation(self):
        """Stop relay operation."""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=5.0)
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        self.logger.info("Relay operation stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """Get relay-specific statistics."""
        stats = super().get_statistics()
        
        # Add LoRaWAN statistics
        lorawan_stats = self.lorawan_emitter.get_statistics()
        stats.update({
            'lorawan_joined': lorawan_stats.get('is_joined', False),
            'lorawan_dev_addr': lorawan_stats.get('dev_addr'),
            'lorawan_duty_cycle': lorawan_stats.get('current_duty_cycle', 0),
            'mqtt_connected': self.mqtt_connected,
            'mqtt_broker': self.mqtt_config.get('broker', 'not_configured'),
            'total_forwarded': self.total_forwarded
        })
        
        return stats