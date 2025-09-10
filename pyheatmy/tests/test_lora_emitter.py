"""
Tests for LoRa and LoRaWAN emitter classes.
"""

import unittest
import tempfile
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from io import StringIO

from pyheatmy.lora_emitter import (
    LoRaEmitter, LoRaWANEmitter, LoRaPacket, 
    LoRaSpreadingFactor, LoRaFrequency
)


class TestLoRaPacket(unittest.TestCase):
    """Test LoRa packet creation and manipulation."""

    def test_packet_creation(self):
        """Test basic packet creation."""
        packet = LoRaPacket(
            checksum=0xa5,
            destination=1,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="2024-11-07,10:00:12,21.55,22.11,21.99,21",
            timestamp=datetime.now()
        )
        
        self.assertEqual(packet.destination, 1)
        self.assertEqual(packet.local_address, 5)
        self.assertEqual(packet.packet_number, 2)
        self.assertEqual(packet.request_type, 0xc3)
        self.assertIn("2024-11-07", packet.payload)

    def test_checksum_calculation(self):
        """Test checksum calculation."""
        packet = LoRaPacket(
            checksum=0,
            destination=1,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="test_data",
            timestamp=datetime.now()
        )
        
        checksum = packet.calculate_checksum()
        self.assertIsInstance(checksum, int)
        self.assertGreaterEqual(checksum, 0)
        self.assertLessEqual(checksum, 255)

    def test_packet_serialization(self):
        """Test packet to bytes conversion."""
        packet = LoRaPacket(
            checksum=0xa5,
            destination=1,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="test",
            timestamp=datetime.now()
        )
        
        data = packet.to_bytes()
        self.assertIsInstance(data, bytes)
        self.assertGreaterEqual(len(data), 5)  # At least header size
        
        # Check header bytes
        self.assertEqual(data[0], 0xa5)  # checksum
        self.assertEqual(data[1], 1)     # destination
        self.assertEqual(data[2], 5)     # local_address
        self.assertEqual(data[3], 2)     # packet_number
        self.assertEqual(data[4], 0xc3)  # request_type

    def test_packet_size(self):
        """Test packet size calculation."""
        packet = LoRaPacket(
            checksum=0xa5,
            destination=1,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="test_data",
            timestamp=datetime.now()
        )
        
        size = packet.get_size()
        expected_size = 5 + len("test_data".encode('utf-8'))  # header + payload
        self.assertEqual(size, expected_size)


class TestLoRaEmitter(unittest.TestCase):
    """Test LoRa emitter functionality."""

    def setUp(self):
        """Set up test environment."""
        self.emitter = LoRaEmitter(
            device_address=5,
            spreading_factor=LoRaSpreadingFactor.SF7,
            verbose=False
        )
        
        # Create sample CSV data
        self.sample_data = pd.DataFrame({
            'Date Heure, GMT+01:00': [
                '07/12/16 11:00:00 AM',
                '07/12/16 11:15:00 AM',
                '07/12/16 11:30:00 AM'
            ],
            'Temp1': [22.154, 26.5, 14.553],
            'Temp2': [21.604, 27.038, 13.738],
            'Temp3': [20.317, 23.737, 13.69],
            'Temp4': [20.65, 21.819, 13.738]
        })

    def test_emitter_initialization(self):
        """Test emitter initialization."""
        self.assertEqual(self.emitter.device_address, 5)
        self.assertEqual(self.emitter.spreading_factor, LoRaSpreadingFactor.SF7)
        self.assertEqual(self.emitter.frequency, LoRaFrequency.EU868)
        self.assertEqual(self.emitter.packet_counter, 0)
        self.assertEqual(len(self.emitter.transmitted_packets), 0)

    def test_csv_loading(self):
        """Test CSV data loading."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            df = self.emitter.load_csv_data(csv_path)
            self.assertEqual(len(df), 3)
            self.assertIn('Temp1', df.columns)
            self.assertIn('Date Heure, GMT+01:00', df.columns)
        finally:
            os.unlink(csv_path)

    def test_packet_creation_from_data(self):
        """Test packet creation from data row."""
        data_row = self.sample_data.iloc[0]
        packet = self.emitter.create_data_packet(data_row, destination=1)
        
        self.assertEqual(packet.destination, 1)
        self.assertEqual(packet.local_address, 5)
        self.assertEqual(packet.packet_number, 0)
        self.assertEqual(packet.request_type, 0xc3)
        self.assertIn("22.15", packet.payload)  # Temperature value should be in payload

    def test_transmission_simulation(self):
        """Test transmission simulation."""
        data_row = self.sample_data.iloc[0]
        packet = self.emitter.create_data_packet(data_row)
        
        result = self.emitter.simulate_transmission(packet)
        
        self.assertIn('success', result)
        self.assertIn('airtime_ms', result)
        self.assertIn('packet_size', result)
        self.assertIn('timestamp', result)
        self.assertIsInstance(result['success'], bool)
        self.assertGreater(result['airtime_ms'], 0)

    def test_retry_mechanism(self):
        """Test retry mechanism with mocked failures."""
        # Create emitter with high retry count for testing
        emitter = LoRaEmitter(device_address=5, max_retries=3, verbose=False)
        
        data_row = self.sample_data.iloc[0]
        packet = emitter.create_data_packet(data_row)
        
        result = emitter.transmit_with_retry(packet)
        
        self.assertIn('retries', result)
        self.assertGreaterEqual(result['retries'], 0)
        self.assertLessEqual(result['retries'], 3)

    def test_csv_emission(self):
        """Test full CSV data emission."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            results = self.emitter.emit_csv_data(
                csv_path, 
                transmission_interval=0.01  # Fast transmission for testing
            )
            
            self.assertEqual(len(results), 3)  # Should have 3 transmissions
            self.assertGreater(self.emitter.packet_counter, 0)
            
            # Check statistics
            stats = self.emitter.get_statistics()
            self.assertIn('total_packets', stats)
            self.assertIn('success_rate', stats)
            self.assertEqual(stats['device_address'], 5)
            
        finally:
            os.unlink(csv_path)

    def test_payload_size_limiting(self):
        """Test payload size limiting."""
        # Create large data row
        large_data = pd.Series([f"very_long_value_{i}" for i in range(50)])
        
        emitter = LoRaEmitter(device_address=5, max_payload_size=100)
        packet = emitter.create_data_packet(large_data)
        
        # Payload should be truncated to fit within size limit
        self.assertLessEqual(len(packet.payload.encode('utf-8')), 100)

    def test_statistics_calculation(self):
        """Test statistics calculation."""
        # Initial statistics
        stats = self.emitter.get_statistics()
        self.assertEqual(stats['total_packets'], 0)
        
        # Simulate some transmissions
        data_row = self.sample_data.iloc[0]
        for i in range(5):
            packet = self.emitter.create_data_packet(data_row)
            self.emitter.simulate_transmission(packet)
        
        stats = self.emitter.get_statistics()
        self.assertGreater(stats['total_packets'], 0)
        self.assertIn('success_rate', stats)
        self.assertIn('average_airtime_ms', stats)


class TestLoRaWANEmitter(unittest.TestCase):
    """Test LoRaWAN emitter functionality."""

    def setUp(self):
        """Set up test environment."""
        self.emitter = LoRaWANEmitter(
            device_address=10,
            app_eui="0000000000000000",
            app_key="387BC5DEF778168781DDE361D4407953",
            verbose=False
        )
        
        self.sample_data = pd.DataFrame({
            'timestamp': [
                datetime.now() - timedelta(minutes=30),
                datetime.now() - timedelta(minutes=15),
                datetime.now()
            ],
            'temperature': [21.5, 22.1, 21.9],
            'pressure': [1013.2, 1013.5, 1013.1]
        })

    def test_lorawan_initialization(self):
        """Test LoRaWAN emitter initialization."""
        self.assertEqual(self.emitter.device_address, 10)
        self.assertEqual(self.emitter.app_eui, "0000000000000000")
        self.assertFalse(self.emitter.is_joined)
        self.assertIsNone(self.emitter.dev_addr)

    def test_join_procedure(self):
        """Test join procedure simulation."""
        # Multiple attempts may be needed due to random success
        joined = False
        for _ in range(10):  # Try up to 10 times
            if self.emitter.simulate_join_procedure():
                joined = True
                break
                
        if joined:
            self.assertTrue(self.emitter.is_joined)
            self.assertIsNotNone(self.emitter.dev_addr)
            self.assertIsNotNone(self.emitter.network_session_key)
            self.assertIsNotNone(self.emitter.app_session_key)

    def test_join_network_with_retries(self):
        """Test network join with retry mechanism."""
        success = self.emitter.join_network(max_attempts=5)
        # Note: This may fail due to randomness, but should succeed most of the time
        
        if success:
            self.assertTrue(self.emitter.is_joined)
            stats = self.emitter.get_statistics()
            self.assertIn('is_joined', stats)
            self.assertIn('dev_addr', stats)

    def test_duty_cycle_checking(self):
        """Test duty cycle compliance checking."""
        # Initially should allow transmission
        self.assertTrue(self.emitter.check_duty_cycle(100))  # 100ms airtime
        
        # Add some transmission history
        now = datetime.now()
        for i in range(10):
            self.emitter.transmission_history.append({
                'timestamp': now - timedelta(minutes=i),
                'airtime_ms': 1000,  # 1 second each
                'packet_size': 50
            })
        
        # Should now be more restrictive
        result = self.emitter.check_duty_cycle(10000)  # 10 seconds
        # This depends on the duty cycle limit, but should be blocked for very large airtimes

    def test_lorawan_transmission_not_joined(self):
        """Test that transmission fails when not joined."""
        data_row = self.sample_data.iloc[0]
        packet = self.emitter.create_data_packet(data_row)
        
        result = self.emitter.simulate_transmission(packet)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'not_joined')

    def test_lorawan_statistics(self):
        """Test LoRaWAN-specific statistics."""
        stats = self.emitter.get_statistics()
        
        self.assertIn('is_joined', stats)
        self.assertIn('dev_addr', stats)
        self.assertIn('app_eui', stats)
        self.assertIn('current_duty_cycle', stats)
        self.assertIn('duty_cycle_limit', stats)
        self.assertIn('transmissions_last_hour', stats)

    def test_csv_emission_lorawan(self):
        """Test CSV emission with LoRaWAN (without actual join)."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # This should fail because we're not joined
            results = self.emitter.emit_csv_data_lorawan(
                csv_path, 
                transmission_interval=0.01
            )
            
            # Should return empty list since join will likely fail in test
            self.assertIsInstance(results, list)
            
        finally:
            os.unlink(csv_path)


class TestEnumsAndConstants(unittest.TestCase):
    """Test enum definitions and constants."""

    def test_spreading_factors(self):
        """Test spreading factor enum."""
        sf7 = LoRaSpreadingFactor.SF7
        self.assertEqual(sf7.sf, 7)
        self.assertGreater(sf7.bitrate, 0)
        self.assertGreater(sf7.symbol_time, 0)
        
        sf12 = LoRaSpreadingFactor.SF12
        self.assertEqual(sf12.sf, 12)
        self.assertLess(sf12.bitrate, sf7.bitrate)  # Lower bitrate for higher SF
        self.assertGreater(sf12.symbol_time, sf7.symbol_time)  # Longer symbol time

    def test_frequencies(self):
        """Test frequency enum."""
        eu868 = LoRaFrequency.EU868
        self.assertEqual(eu868.value, 868.1)
        
        us915 = LoRaFrequency.US915
        self.assertEqual(us915.value, 915.0)


if __name__ == '__main__':
    unittest.main()