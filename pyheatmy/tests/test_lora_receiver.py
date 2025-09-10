"""
Tests for LoRa and LoRaWAN receiver classes.
"""

import unittest
import tempfile
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime, timedelta
from io import StringIO

from pyheatmy.lora_emitter import (
    LoRaEmitter, LoRaWANEmitter, LoRaPacket, 
    LoRaSpreadingFactor, LoRaFrequency
)
from pyheatmy.lora_receiver import (
    LoRaReceiver, LoRaWANReceiver, ReceivedPacket
)


class TestReceivedPacket(unittest.TestCase):
    """Test ReceivedPacket dataclass."""

    def test_received_packet_creation(self):
        """Test basic received packet creation."""
        original_packet = LoRaPacket(
            checksum=0xa5,
            destination=1,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="test_data",
            timestamp=datetime.now()
        )
        
        received_packet = ReceivedPacket(
            original_packet=original_packet,
            received_timestamp=datetime.now(),
            rssi=-85.0,
            snr=8.5
        )
        
        self.assertEqual(received_packet.original_packet, original_packet)
        self.assertIsInstance(received_packet.received_timestamp, datetime)
        self.assertEqual(received_packet.rssi, -85.0)
        self.assertEqual(received_packet.snr, 8.5)
        self.assertTrue(received_packet.reception_success)


class TestLoRaReceiver(unittest.TestCase):
    """Test LoRa receiver functionality."""

    def setUp(self):
        """Set up test environment."""
        self.receiver = LoRaReceiver(
            device_address=1,
            spreading_factor=LoRaSpreadingFactor.SF7,
            reception_success_rate=1.0,  # 100% for testing
            verbose=False
        )
        
        self.emitter = LoRaEmitter(
            device_address=5,
            spreading_factor=LoRaSpreadingFactor.SF7,
            verbose=False
        )
        
        # Create sample data
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

    def test_receiver_initialization(self):
        """Test receiver initialization."""
        self.assertEqual(self.receiver.device_address, 1)
        self.assertEqual(self.receiver.spreading_factor, LoRaSpreadingFactor.SF7)
        self.assertEqual(self.receiver.reception_success_rate, 1.0)
        self.assertEqual(self.receiver.total_received, 0)
        self.assertEqual(len(self.receiver.received_packets), 0)

    def test_packet_reception_simulation(self):
        """Test packet reception simulation."""
        # Create and transmit a packet
        data_row = self.sample_data.iloc[0]
        packet = self.emitter.create_data_packet(data_row, destination=self.receiver.device_address)
        tx_result = self.emitter.simulate_transmission(packet)
        
        # Simulate reception
        rx_packet = self.receiver.simulate_packet_reception(tx_result)
        
        if tx_result['success']:  # Only test if transmission was successful
            self.assertIsNotNone(rx_packet)
            self.assertEqual(rx_packet.original_packet, packet)
            self.assertIsInstance(rx_packet.received_timestamp, datetime)
            self.assertTrue(rx_packet.reception_success)
            self.assertEqual(self.receiver.total_received, 1)

    def test_reception_failure(self):
        """Test reception of failed transmissions."""
        # Create a failed transmission result
        packet = LoRaPacket(
            checksum=0,
            destination=1,
            local_address=5,
            packet_number=1,
            request_type=0xc3,
            payload="test",
            timestamp=datetime.now()
        )
        
        failed_tx = {
            'packet': packet,
            'success': False,
            'airtime_ms': 100,
            'packet_size': 10,
            'timestamp': datetime.now(),
            'retries': 0
        }
        
        rx_packet = self.receiver.simulate_packet_reception(failed_tx)
        self.assertIsNone(rx_packet)
        self.assertEqual(self.receiver.total_received, 0)

    def test_acknowledgment_sending(self):
        """Test acknowledgment sending."""
        # Create received packet
        original_packet = LoRaPacket(
            checksum=0xa5,
            destination=self.receiver.device_address,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="test_data",
            timestamp=datetime.now()
        )
        
        received_packet = ReceivedPacket(
            original_packet=original_packet,
            received_timestamp=datetime.now()
        )
        
        # Send acknowledgment
        ack_success = self.receiver.send_acknowledgment(received_packet)
        self.assertIsInstance(ack_success, bool)

    def test_timestamp_addition(self):
        """Test reception timestamp addition."""
        original_packet = LoRaPacket(
            checksum=0xa5,
            destination=1,
            local_address=5,
            packet_number=2,
            request_type=0xc3,
            payload="2024-11-07,10:00:12,21.55,22.11,21.99,21",
            timestamp=datetime.now()
        )
        
        received_packet = ReceivedPacket(
            original_packet=original_packet,
            received_timestamp=datetime.now()
        )
        
        updated_payload = self.receiver.add_reception_timestamp(received_packet)
        
        self.assertIn("RX_TIME:", updated_payload)
        self.assertIn(original_packet.payload, updated_payload)
        self.assertTrue(updated_payload.startswith(original_packet.payload))

    def test_packet_processing(self):
        """Test packet processing from queue."""
        # Create and add packets to queue
        for i in range(3):
            original_packet = LoRaPacket(
                checksum=0xa5,
                destination=1,
                local_address=5,
                packet_number=i,
                request_type=0xc3,
                payload=f"test_data_{i}",
                timestamp=datetime.now()
            )
            
            received_packet = ReceivedPacket(
                original_packet=original_packet,
                received_timestamp=datetime.now()
            )
            
            self.receiver.receive_queue.put(received_packet)
        
        # Process packets
        processed = self.receiver.process_received_packets(send_acks=False)
        
        self.assertEqual(len(processed), 3)
        self.assertTrue(self.receiver.receive_queue.empty())

    def test_csv_data_saving(self):
        """Test saving received data to CSV."""
        # Create some received packets
        for i in range(2):
            original_packet = LoRaPacket(
                checksum=0xa5,
                destination=1,
                local_address=5,
                packet_number=i,
                request_type=0xc3,
                payload=f"2024-11-07,10:0{i}:12,21.5{i},22.1{i},21.9{i},21.0{i},1013.{i}5",
                timestamp=datetime.now()
            )
            
            received_packet = ReceivedPacket(
                original_packet=original_packet,
                received_timestamp=datetime.now(),
                rssi=-80.0 - i,
                snr=10.0 - i
            )
            
            self.receiver.received_packets.append(received_packet)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            saved_count = self.receiver.save_received_data_to_csv(csv_path, append=False)
            self.assertEqual(saved_count, 2)
            
            # Verify file was created and has content
            self.assertTrue(os.path.exists(csv_path))
            
            # Load and verify content
            df = pd.read_csv(csv_path)
            self.assertEqual(len(df), 2)
            self.assertIn('sender_address', df.columns)
            self.assertIn('received_timestamp', df.columns)
            self.assertIn('rssi_dbm', df.columns)
            
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_statistics(self):
        """Test statistics calculation."""
        # Initial statistics
        stats = self.receiver.get_statistics()
        self.assertEqual(stats['total_received'], 0)
        self.assertEqual(stats['device_address'], 1)
        
        # Simulate some reception
        self.receiver.total_received = 5
        self.receiver.reception_errors = 1
        
        stats = self.receiver.get_statistics()
        self.assertEqual(stats['total_received'], 5)
        self.assertEqual(stats['reception_errors'], 1)
        self.assertAlmostEqual(stats['reception_rate'], 5/6, places=2)

    def test_queue_overflow(self):
        """Test behavior when receive queue is full."""
        # Create receiver with small queue
        small_receiver = LoRaReceiver(
            device_address=1,
            max_queue_size=2,
            verbose=False
        )
        
        # Fill queue beyond capacity
        for i in range(5):
            packet = LoRaPacket(
                checksum=0,
                destination=1,
                local_address=5,
                packet_number=i,
                request_type=0xc3,
                payload=f"data_{i}",
                timestamp=datetime.now()
            )
            
            tx_result = {
                'packet': packet,
                'success': True,
                'airtime_ms': 100,
                'packet_size': 10,
                'timestamp': datetime.now(),
                'retries': 0
            }
            
            small_receiver.simulate_packet_reception(tx_result)
        
        # Should have reception errors due to queue overflow
        self.assertGreater(small_receiver.reception_errors, 0)


class TestLoRaWANReceiver(unittest.TestCase):
    """Test LoRaWAN receiver functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create receiver without MQTT to avoid connection issues in tests
        self.receiver = LoRaWANReceiver(
            device_address=10,
            app_eui="0000000000000000",
            app_key="387BC5DEF778168781DDE361D4407953",
            verbose=False
        )
        
        self.emitter = LoRaEmitter(
            device_address=5,
            verbose=False
        )

    def test_lorawan_receiver_initialization(self):
        """Test LoRaWAN receiver initialization."""
        self.assertEqual(self.receiver.device_address, 10)
        self.assertIsNotNone(self.receiver.lorawan_emitter)
        self.assertFalse(self.receiver.lorawan_emitter.is_joined)
        self.assertEqual(self.receiver.total_forwarded, 0)

    def test_lorawan_join(self):
        """Test LoRaWAN network join."""
        # May succeed or fail due to randomness in simulation
        joined = self.receiver.join_lorawan_network(max_attempts=3)
        self.assertIsInstance(joined, bool)
        
        if joined:
            self.assertTrue(self.receiver.lorawan_emitter.is_joined)

    def test_packet_forwarding_not_joined(self):
        """Test packet forwarding when not joined to LoRaWAN."""
        original_packet = LoRaPacket(
            checksum=0xa5,
            destination=10,
            local_address=5,
            packet_number=1,
            request_type=0xc3,
            payload="test_data",
            timestamp=datetime.now()
        )
        
        received_packet = ReceivedPacket(
            original_packet=original_packet,
            received_timestamp=datetime.now()
        )
        
        # Should fail when not joined
        result = self.receiver.forward_via_lorawan(received_packet)
        self.assertFalse(result.get('success', True))

    def test_mqtt_config(self):
        """Test MQTT configuration."""
        mqtt_config = {
            'broker': 'test.example.com',
            'port': 1883,
            'topic': 'test/topic'
        }
        
        mqtt_receiver = LoRaWANReceiver(
            device_address=11,
            mqtt_config=mqtt_config,
            verbose=False
        )
        
        self.assertEqual(mqtt_receiver.mqtt_config, mqtt_config)

    def test_relay_processor_not_joined(self):
        """Test relay packet processor when not joined."""
        original_packet = LoRaPacket(
            checksum=0xa5,
            destination=10,
            local_address=5,
            packet_number=1,
            request_type=0xc3,
            payload="test_data",
            timestamp=datetime.now()
        )
        
        received_packet = ReceivedPacket(
            original_packet=original_packet,
            received_timestamp=datetime.now()
        )
        
        # Should fail when not joined
        success = self.receiver.relay_packet_processor(received_packet)
        self.assertFalse(success)

    def test_relay_operation_lifecycle(self):
        """Test starting and stopping relay operation."""
        # Start relay (may fail to join)
        started = self.receiver.start_relay_operation(auto_process=False)
        self.assertIsInstance(started, bool)
        
        # Stop relay
        self.receiver.stop_relay_operation()
        self.assertFalse(self.receiver.is_listening)

    def test_lorawan_statistics(self):
        """Test LoRaWAN-specific statistics."""
        stats = self.receiver.get_statistics()
        
        # Check for LoRaWAN-specific fields
        self.assertIn('lorawan_joined', stats)
        self.assertIn('lorawan_dev_addr', stats)
        self.assertIn('lorawan_duty_cycle', stats)
        self.assertIn('mqtt_connected', stats)
        self.assertIn('total_forwarded', stats)

    def test_timestamp_addition_in_forwarding(self):
        """Test that timestamp is added during forwarding."""
        original_packet = LoRaPacket(
            checksum=0xa5,
            destination=10,
            local_address=5,
            packet_number=1,
            request_type=0xc3,
            payload="2024-11-07,10:00:12,21.55,22.11",
            timestamp=datetime.now()
        )
        
        received_packet = ReceivedPacket(
            original_packet=original_packet,
            received_timestamp=datetime.now()
        )
        
        # Get updated payload
        updated_payload = self.receiver.add_reception_timestamp(received_packet)
        
        # Verify timestamp was added
        self.assertIn("RX_TIME:", updated_payload)
        self.assertIn(original_packet.payload, updated_payload)


class TestIntegration(unittest.TestCase):
    """Integration tests for emitter-receiver communication."""

    def test_end_to_end_communication(self):
        """Test complete emitter to receiver communication."""
        # Setup
        emitter = LoRaEmitter(device_address=5, verbose=False)
        receiver = LoRaReceiver(
            device_address=1, 
            reception_success_rate=1.0,  # Ensure reception for test
            verbose=False
        )
        
        # Create test data
        test_data = pd.Series({
            'timestamp': '2024-11-07 10:00:00',
            'temp1': 21.5,
            'temp2': 22.1,
            'pressure': 1013.25
        })
        
        # Transmit
        packet = emitter.create_data_packet(test_data, destination=receiver.device_address)
        tx_result = emitter.simulate_transmission(packet)
        
        # Receive
        if tx_result['success']:
            rx_packet = receiver.simulate_packet_reception(tx_result)
            
            # Verify reception
            self.assertIsNotNone(rx_packet)
            self.assertEqual(rx_packet.original_packet.packet_number, packet.packet_number)
            
            # Process
            processed = receiver.process_received_packets()
            self.assertEqual(len(processed), 1)
            
            # Verify statistics
            self.assertEqual(receiver.total_received, 1)
            self.assertEqual(emitter.get_statistics()['successful_packets'], 1)

    def test_multiple_packet_transmission(self):
        """Test transmission of multiple packets."""
        emitter = LoRaEmitter(device_address=5, verbose=False)
        receiver = LoRaReceiver(device_address=1, verbose=False)
        
        # Create multiple test packets
        num_packets = 5
        for i in range(num_packets):
            test_data = pd.Series({
                'timestamp': f'2024-11-07 10:0{i}:00',
                'temp': 20.0 + i,
                'id': i
            })
            
            packet = emitter.create_data_packet(test_data, destination=receiver.device_address)
            tx_result = emitter.simulate_transmission(packet)
            
            if tx_result['success']:
                receiver.simulate_packet_reception(tx_result)
        
        # Verify some packets were received
        self.assertGreater(receiver.total_received, 0)
        self.assertLessEqual(receiver.total_received, num_packets)


if __name__ == '__main__':
    unittest.main()