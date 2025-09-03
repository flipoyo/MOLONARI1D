"""
LoRa and LoRaWAN emitter simulation for MOLONARI1D sensor data.

This module provides classes to simulate LoRa and LoRaWAN transmission behavior
from sensor data stored in CSV files. It emulates the communication protocols
used by the MOLONARI1D project's Arduino MKR WAN 1310 devices.
"""

import pandas as pd
import numpy as np
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import random


class LoRaSpreadingFactor(Enum):
    """LoRa spreading factors with their characteristics."""
    SF7 = (7, 5469, 109.38)    # (SF, bps, ms/symbol)
    SF8 = (8, 3125, 219.77)
    SF9 = (9, 1758, 439.45)
    SF10 = (10, 977, 878.91)
    SF11 = (11, 488, 1757.81)
    SF12 = (12, 244, 3515.63)

    def __init__(self, sf: int, bitrate: int, symbol_time: float):
        self.sf = sf
        self.bitrate = bitrate  # bits per second
        self.symbol_time = symbol_time  # milliseconds per symbol


class LoRaFrequency(Enum):
    """Standard LoRa frequency bands."""
    EU868 = 868.1  # MHz - European band
    US915 = 915.0  # MHz - North American band
    AS923 = 923.0  # MHz - Asian band


@dataclass
class LoRaPacket:
    """Represents a LoRa packet structure as used in MOLONARI1D."""
    checksum: int
    destination: int
    local_address: int
    packet_number: int
    request_type: int
    payload: str
    timestamp: datetime

    def calculate_checksum(self) -> int:
        """Calculate checksum for packet integrity."""
        data = f"{self.destination}{self.local_address}{self.packet_number}{self.request_type}{self.payload}"
        return int(hashlib.md5(data.encode()).hexdigest()[:2], 16)

    def to_bytes(self) -> bytes:
        """Convert packet to byte representation for transmission."""
        header = bytes([
            self.checksum,
            self.destination,
            self.local_address,
            self.packet_number,
            self.request_type
        ])
        payload_bytes = self.payload.encode('utf-8')
        return header + payload_bytes

    def get_size(self) -> int:
        """Get packet size in bytes."""
        return len(self.to_bytes())


class LoRaEmitter:
    """
    Simulates a LoRa device emitting sensor data from CSV files.
    
    This class emulates the behavior of Arduino MKR WAN 1310 devices used in the 
    MOLONARI1D project for local LoRa communication between sensors and relays.
    """

    def __init__(
        self,
        device_address: int,
        spreading_factor: LoRaSpreadingFactor = LoRaSpreadingFactor.SF7,
        frequency: LoRaFrequency = LoRaFrequency.EU868,
        power: int = 14,  # dBm
        max_payload_size: int = 200,
        max_retries: int = 6,
        retry_delay_base: float = 1.0,  # seconds
        verbose: bool = False
    ):
        """
        Initialize LoRa emitter.
        
        Parameters:
        -----------
        device_address : int
            Unique address for this device (0-255)
        spreading_factor : LoRaSpreadingFactor
            LoRa spreading factor (affects range vs data rate)
        frequency : LoRaFrequency  
            Transmission frequency band
        power : int
            Transmission power in dBm (2-20)
        max_payload_size : int
            Maximum payload size in bytes
        max_retries : int
            Maximum retry attempts for failed transmissions
        retry_delay_base : float
            Base delay for exponential backoff retries
        verbose : bool
            Enable verbose logging
        """
        self.device_address = device_address
        self.spreading_factor = spreading_factor
        self.frequency = frequency
        self.power = power
        self.max_payload_size = max_payload_size
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        self.verbose = verbose
        
        self.packet_counter = 0
        self.transmitted_packets = []
        self.failed_transmissions = []
        
        # Setup logging
        self.logger = logging.getLogger(f"LoRaEmitter_{device_address}")
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def load_csv_data(self, csv_path: str, timestamp_col: str = None, 
                      value_cols: List[str] = None) -> pd.DataFrame:
        """
        Load sensor data from CSV file.
        
        Parameters:
        -----------
        csv_path : str
            Path to CSV file containing sensor data
        timestamp_col : str, optional
            Name of timestamp column (auto-detected if None)
        value_cols : List[str], optional
            Names of value columns (all numeric columns if None)
            
        Returns:
        --------
        pd.DataFrame
            Loaded and processed sensor data
        """
        try:
            df = pd.read_csv(csv_path)
            
            # Auto-detect timestamp column if not specified
            if timestamp_col is None:
                for col in df.columns:
                    if 'date' in col.lower() or 'time' in col.lower():
                        timestamp_col = col
                        break
                        
            if timestamp_col and timestamp_col in df.columns:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
                df = df.dropna(subset=[timestamp_col])
                df = df.sort_values(timestamp_col)
                
            # Auto-detect value columns if not specified
            if value_cols is None:
                value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
            self.logger.info(f"Loaded {len(df)} records from {csv_path}")
            self.logger.info(f"Timestamp column: {timestamp_col}")
            self.logger.info(f"Value columns: {value_cols}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load CSV data: {e}")
            raise

    def create_data_packet(self, data_row: pd.Series, destination: int = 1, 
                          request_type: int = 0xc3) -> LoRaPacket:
        """
        Create a LoRa packet from sensor data.
        
        Parameters:
        -----------
        data_row : pd.Series
            Row of sensor data from DataFrame
        destination : int
            Destination device address
        request_type : int
            Type of request (0xc3 for data transfer)
            
        Returns:
        --------
        LoRaPacket
            Formatted packet ready for transmission
        """
        # Format payload similar to Arduino code
        # "2024-11-07,10:00:12,21.55,22.11,21.99,21"
        payload_parts = []
        
        for value in data_row.values:
            if pd.isna(value):
                continue
            if isinstance(value, (int, float)):
                payload_parts.append(f"{value:.2f}")
            else:
                payload_parts.append(str(value))
                
        payload = ",".join(payload_parts)
        
        # Truncate if too long
        if len(payload.encode('utf-8')) > self.max_payload_size:
            payload = payload[:self.max_payload_size].rsplit(',', 1)[0]
            
        packet = LoRaPacket(
            checksum=0,  # Will be calculated
            destination=destination,
            local_address=self.device_address,
            packet_number=self.packet_counter % 256,
            request_type=request_type,
            payload=payload,
            timestamp=datetime.now()
        )
        
        packet.checksum = packet.calculate_checksum()
        self.packet_counter += 1
        
        return packet

    def simulate_transmission(self, packet: LoRaPacket) -> Dict[str, Any]:
        """
        Simulate packet transmission with realistic timing and potential failures.
        
        Parameters:
        -----------
        packet : LoRaPacket
            Packet to transmit
            
        Returns:
        --------
        Dict[str, Any]
            Transmission result with timing and success information
        """
        # Calculate transmission time based on packet size and spreading factor
        packet_size = packet.get_size()
        symbol_time_ms = self.spreading_factor.symbol_time
        preamble_symbols = 8
        header_symbols = 4.25
        
        # Simplified airtime calculation
        payload_symbols = max(1, (packet_size * 8 - 4 * self.spreading_factor.sf + 28) / 
                             (4 * self.spreading_factor.sf))
        total_symbols = preamble_symbols + header_symbols + payload_symbols
        airtime_ms = total_symbols * symbol_time_ms
        
        # Simulate transmission delay
        time.sleep(airtime_ms / 1000)
        
        # Simulate potential failures (based on spreading factor and power)
        # Higher SF and power = better reliability
        base_success_rate = 0.85
        sf_bonus = (self.spreading_factor.sf - 7) * 0.02
        power_bonus = (self.power - 2) * 0.005
        success_rate = min(0.98, base_success_rate + sf_bonus + power_bonus)
        
        success = random.random() < success_rate
        
        result = {
            'packet': packet,
            'success': success,
            'airtime_ms': airtime_ms,
            'packet_size': packet_size,
            'timestamp': datetime.now(),
            'retries': 0
        }
        
        if success:
            self.transmitted_packets.append(result)
            self.logger.debug(f"Packet {packet.packet_number} transmitted successfully "
                            f"({airtime_ms:.1f}ms, {packet_size} bytes)")
        else:
            self.logger.warning(f"Packet {packet.packet_number} transmission failed")
            
        return result

    def transmit_with_retry(self, packet: LoRaPacket) -> Dict[str, Any]:
        """
        Attempt packet transmission with exponential backoff retry.
        
        Parameters:
        -----------
        packet : LoRaPacket
            Packet to transmit
            
        Returns:
        --------
        Dict[str, Any]
            Final transmission result after retries
        """
        for attempt in range(self.max_retries + 1):
            result = self.simulate_transmission(packet)
            result['retries'] = attempt
            
            if result['success']:
                if attempt > 0:
                    self.logger.info(f"Packet {packet.packet_number} succeeded after {attempt} retries")
                return result
                
            if attempt < self.max_retries:
                delay = self.retry_delay_base * (2 ** attempt)
                self.logger.debug(f"Retry {attempt + 1} in {delay:.1f}s...")
                time.sleep(delay)
                
        # All retries failed
        self.failed_transmissions.append(result)
        self.logger.error(f"Packet {packet.packet_number} failed after {self.max_retries} retries")
        return result

    def emit_csv_data(self, csv_path: str, destination: int = 1, 
                     transmission_interval: float = 0.1, **csv_kwargs) -> List[Dict[str, Any]]:
        """
        Load CSV data and emit all records as LoRa packets.
        
        Parameters:
        -----------
        csv_path : str
            Path to CSV file
        destination : int
            Destination device address  
        transmission_interval : float
            Delay between transmissions in seconds
        **csv_kwargs
            Additional arguments passed to load_csv_data()
            
        Returns:
        --------
        List[Dict[str, Any]]
            List of transmission results
        """
        df = self.load_csv_data(csv_path, **csv_kwargs)
        results = []
        
        self.logger.info(f"Starting emission of {len(df)} packets to device {destination}")
        
        for i, (_, row) in enumerate(df.iterrows()):
            packet = self.create_data_packet(row, destination)
            result = self.transmit_with_retry(packet)
            results.append(result)
            
            if i < len(df) - 1 and transmission_interval > 0:
                time.sleep(transmission_interval)
                
        self.logger.info(f"Emission complete: {self.get_success_rate():.1%} success rate")
        return results

    def get_success_rate(self) -> float:
        """Get overall transmission success rate."""
        total = len(self.transmitted_packets) + len(self.failed_transmissions)
        return len(self.transmitted_packets) / total if total > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed transmission statistics."""
        successful = len(self.transmitted_packets)
        failed = len(self.failed_transmissions)
        total = successful + failed
        
        if total == 0:
            return {'total_packets': 0}
            
        avg_airtime = np.mean([r['airtime_ms'] for r in self.transmitted_packets]) if successful > 0 else 0
        avg_retries = np.mean([r['retries'] for r in self.transmitted_packets + self.failed_transmissions])
        
        return {
            'total_packets': total,
            'successful_packets': successful,
            'failed_packets': failed,
            'success_rate': successful / total,
            'average_airtime_ms': avg_airtime,
            'average_retries': avg_retries,
            'device_address': self.device_address,
            'spreading_factor': self.spreading_factor.sf,
            'frequency_mhz': self.frequency.value,
            'power_dbm': self.power
        }


class LoRaWANEmitter(LoRaEmitter):
    """
    Extends LoRaEmitter to simulate LoRaWAN network behavior.
    
    Adds LoRaWAN-specific features like join procedures, duty cycles,
    and network server interaction simulation.
    """

    def __init__(
        self,
        device_address: int,
        app_eui: str = "0000000000000000",
        app_key: str = "387BC5DEF778168781DDE361D4407953",
        duty_cycle_limit: float = 0.01,  # 1% duty cycle limit
        join_retry_interval: float = 60.0,  # seconds
        **kwargs
    ):
        """
        Initialize LoRaWAN emitter.
        
        Parameters:
        -----------
        device_address : int
            Device address
        app_eui : str
            Application EUI for OTAA
        app_key : str
            Application key for OTAA
        duty_cycle_limit : float
            Maximum duty cycle (fraction)
        join_retry_interval : float
            Interval between join attempts
        **kwargs
            Additional arguments passed to LoRaEmitter
        """
        super().__init__(device_address, **kwargs)
        
        self.app_eui = app_eui
        self.app_key = app_key
        self.duty_cycle_limit = duty_cycle_limit
        self.join_retry_interval = join_retry_interval
        
        self.is_joined = False
        self.dev_addr = None
        self.network_session_key = None
        self.app_session_key = None
        
        self.duty_cycle_usage = 0.0
        self.last_transmission_time = None
        self.transmission_history = []

    def simulate_join_procedure(self) -> bool:
        """
        Simulate OTAA join procedure.
        
        Returns:
        --------
        bool
            True if join successful
        """
        self.logger.info("Attempting LoRaWAN join (OTAA)...")
        
        # Simulate join request transmission
        join_packet = LoRaPacket(
            checksum=0,
            destination=0x00,  # Network server
            local_address=self.device_address,
            packet_number=0,
            request_type=0x00,  # Join request
            payload=f"JOIN_REQUEST:{self.app_eui}",
            timestamp=datetime.now()
        )
        
        # Simulate join delay and potential failure
        time.sleep(1.0)  # Join processing delay
        
        join_success = random.random() < 0.9  # 90% join success rate
        
        if join_success:
            self.is_joined = True
            self.dev_addr = f"260B{random.randint(0x1000, 0xFFFF):04X}"
            self.network_session_key = f"NwkSKey_{random.randint(1000, 9999)}"
            self.app_session_key = f"AppSKey_{random.randint(1000, 9999)}"
            
            self.logger.info(f"Join successful! DevAddr: {self.dev_addr}")
            return True
        else:
            self.logger.warning("Join failed, will retry...")
            return False

    def join_network(self, max_attempts: int = 5) -> bool:
        """
        Attempt to join the LoRaWAN network with retries.
        
        Parameters:
        -----------
        max_attempts : int
            Maximum join attempts
            
        Returns:
        --------
        bool
            True if successfully joined
        """
        for attempt in range(max_attempts):
            if self.simulate_join_procedure():
                return True
                
            if attempt < max_attempts - 1:
                self.logger.info(f"Join attempt {attempt + 1} failed, retrying in {self.join_retry_interval}s")
                time.sleep(self.join_retry_interval)
                
        self.logger.error(f"Failed to join network after {max_attempts} attempts")
        return False

    def check_duty_cycle(self, airtime_ms: float) -> bool:
        """
        Check if transmission would violate duty cycle limits.
        
        Parameters:
        -----------
        airtime_ms : float
            Airtime of proposed transmission
            
        Returns:
        --------
        bool
            True if transmission is allowed
        """
        now = datetime.now()
        
        # Remove old transmissions (beyond 1 hour window)
        cutoff = now - timedelta(hours=1)
        self.transmission_history = [t for t in self.transmission_history if t['timestamp'] > cutoff]
        
        # Calculate current usage in the last hour
        total_airtime = sum(t['airtime_ms'] for t in self.transmission_history)
        hour_ms = 60 * 60 * 1000
        current_usage = total_airtime / hour_ms
        
        # Check if new transmission would exceed limit
        new_usage = (total_airtime + airtime_ms) / hour_ms
        
        return new_usage <= self.duty_cycle_limit

    def simulate_transmission(self, packet: LoRaPacket) -> Dict[str, Any]:
        """Override to add LoRaWAN-specific behavior."""
        if not self.is_joined:
            self.logger.error("Cannot transmit - not joined to network")
            return {
                'packet': packet,
                'success': False,
                'error': 'not_joined',
                'timestamp': datetime.now(),
                'retries': 0
            }
            
        # Get base transmission result
        result = super().simulate_transmission(packet)
        
        # Check duty cycle compliance
        if not self.check_duty_cycle(result['airtime_ms']):
            self.logger.warning(f"Transmission blocked by duty cycle limit")
            result['success'] = False
            result['error'] = 'duty_cycle_exceeded'
            return result
            
        # Record transmission for duty cycle tracking
        if result['success']:
            self.transmission_history.append({
                'timestamp': datetime.now(),
                'airtime_ms': result['airtime_ms'],
                'packet_size': result['packet_size']
            })
            
        # Add LoRaWAN-specific fields
        result.update({
            'dev_addr': self.dev_addr,
            'confirmed': True,  # Confirmed uplink
            'fcnt': self.packet_counter - 1,  # Frame counter
        })
        
        return result

    def emit_csv_data_lorawan(self, csv_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Emit CSV data over LoRaWAN with join procedure.
        
        Parameters:
        -----------
        csv_path : str
            Path to CSV file
        **kwargs
            Additional arguments passed to emit_csv_data()
            
        Returns:
        --------
        List[Dict[str, Any]]
            List of transmission results
        """
        # Attempt to join network first
        if not self.is_joined:
            if not self.join_network():
                self.logger.error("Cannot start transmission - failed to join network")
                return []
                
        self.logger.info("Starting LoRaWAN data transmission...")
        return self.emit_csv_data(csv_path, **kwargs)

    def get_statistics(self) -> Dict[str, Any]:
        """Get LoRaWAN-specific statistics."""
        stats = super().get_statistics()
        
        # Calculate duty cycle usage
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        recent_transmissions = [t for t in self.transmission_history if t['timestamp'] > cutoff]
        total_airtime = sum(t['airtime_ms'] for t in recent_transmissions)
        hour_ms = 60 * 60 * 1000
        current_duty_cycle = total_airtime / hour_ms
        
        stats.update({
            'is_joined': self.is_joined,
            'dev_addr': self.dev_addr,
            'app_eui': self.app_eui,
            'current_duty_cycle': current_duty_cycle,
            'duty_cycle_limit': self.duty_cycle_limit,
            'transmissions_last_hour': len(recent_transmissions)
        })
        
        return stats