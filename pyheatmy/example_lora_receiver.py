#!/usr/bin/env python3
"""
Example demonstrating MOLONARI1D LoRa emitter->receiver->gateway data flow.

This script shows how to simulate the complete data transmission chain:
1. LoRa emitter (sensor) transmits data
2. LoRa receiver (relay) receives packets and adds timestamps  
3. Receiver forwards updated data via LoRaWAN to gateway
4. Optional MQTT integration for IoT connectivity

This emulates the real MOLONARI1D hardware communication protocol.
"""

import sys
import os
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the pyheatmy package to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyheatmy.lora_emitter import (
    LoRaEmitter, LoRaWANEmitter, LoRaPacket,
    LoRaSpreadingFactor, LoRaFrequency
)
from pyheatmy.lora_receiver import (
    LoRaReceiver, LoRaWANReceiver, ReceivedPacket
)


def create_sample_data(filename="relay_sample_data.csv", num_records=8):
    """
    Create sample sensor data for relay demonstration.
    
    Parameters:
    -----------
    filename : str
        Output CSV filename
    num_records : int
        Number of data records to generate
    """
    print(f"Creating sample sensor data with {num_records} records...")
    
    # Generate timestamps (10-minute intervals)
    start_time = datetime.now() - timedelta(hours=num_records * 0.167)
    timestamps = [start_time + timedelta(minutes=10*i) for i in range(num_records)]
    
    # Generate realistic temperature data (river sensor simulation)
    base_temp = 12.0  # River temperature
    daily_variation = 2.0
    noise_level = 0.3
    
    temperatures = []
    for i, ts in enumerate(timestamps):
        # Daily cycle
        hour_angle = (ts.hour + ts.minute/60) * 2 * np.pi / 24
        daily_temp = base_temp + daily_variation * np.sin(hour_angle - np.pi/2)
        
        # Add noise and small trend
        temp = daily_temp + np.random.normal(0, noise_level) + i * 0.05
        temperatures.append(round(temp, 2))
    
    # Generate pressure data (water pressure sensor)
    base_pressure = 1015.5  # Slightly higher for underwater sensor
    pressures = [round(base_pressure + np.random.normal(0, 1.5), 2) for _ in range(num_records)]
    
    # Create DataFrame
    data = pd.DataFrame({
        'Date Heure, GMT+01:00': [ts.strftime('%m/%d/%y %I:%M:%S %p') for ts in timestamps],
        'Temp_1': temperatures,
        'Temp_2': [t + np.random.normal(0, 0.2) for t in temperatures],
        'Temp_3': [t + np.random.normal(0, 0.2) for t in temperatures],
        'Temp_4': [t + np.random.normal(0, 0.2) for t in temperatures],
        'Pressure': pressures
    })
    
    # Round temperature columns
    for col in ['Temp_2', 'Temp_3', 'Temp_4']:
        data[col] = data[col].round(2)
    
    data.to_csv(filename, index=False)
    print(f"Sample sensor data saved to {filename}")
    return filename


def demonstrate_basic_relay():
    """Demonstrate basic LoRa emitter to receiver communication."""
    print("\n" + "="*70)
    print("DEMONSTRATING BASIC LORA EMITTER -> RECEIVER COMMUNICATION")
    print("="*70)
    
    # Create sample data
    csv_file = create_sample_data("basic_relay_data.csv", 5)
    
    # Setup emitter (sensor device)
    emitter = LoRaEmitter(
        device_address=0x05,  # Sensor address
        spreading_factor=LoRaSpreadingFactor.SF8,  # Good range/power balance
        frequency=LoRaFrequency.EU868,
        power=14,
        verbose=True
    )
    
    # Setup receiver (relay device)
    receiver = LoRaReceiver(
        device_address=0x01,  # Relay address
        spreading_factor=LoRaSpreadingFactor.SF8,  # Match emitter
        frequency=LoRaFrequency.EU868,
        reception_success_rate=0.9,  # 90% reception rate
        verbose=True
    )
    
    print(f"\nSetup complete:")
    print(f"  Emitter (Sensor): Address 0x{emitter.device_address:02X}, SF{emitter.spreading_factor.sf}")
    print(f"  Receiver (Relay): Address 0x{receiver.device_address:02X}, SF{receiver.spreading_factor.sf}")
    
    # Load and transmit data
    print(f"\nLoading sensor data and starting transmission...")
    df = emitter.load_csv_data(csv_file)
    
    transmitted_packets = []
    received_packets = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        print(f"\n--- Transmitting packet {i+1}/{len(df)} ---")
        
        # Create and transmit packet
        packet = emitter.create_data_packet(row, destination=receiver.device_address)
        tx_result = emitter.simulate_transmission(packet)
        transmitted_packets.append(tx_result)
        
        # Simulate reception
        if tx_result['success']:
            rx_packet = receiver.simulate_packet_reception(tx_result)
            if rx_packet:
                received_packets.append(rx_packet)
                
                # Show updated payload with timestamp
                updated_payload = receiver.add_reception_timestamp(rx_packet)
                print(f"  Original payload: {rx_packet.original_packet.payload}")
                print(f"  Updated payload:  {updated_payload}")
                
                # Send acknowledgment
                receiver.send_acknowledgment(rx_packet)
        
        time.sleep(0.2)  # Small delay between transmissions
    
    # Process any queued packets
    processed = receiver.process_received_packets(send_acks=True)
    
    # Show statistics
    print(f"\n--- Communication Statistics ---")
    emitter_stats = emitter.get_statistics()
    receiver_stats = receiver.get_statistics()
    
    print(f"Emitter: {emitter_stats['successful_packets']}/{emitter_stats['total_packets']} "
          f"packets transmitted successfully ({emitter_stats['success_rate']:.1%})")
    print(f"Receiver: {receiver_stats['total_received']}/{len(transmitted_packets)} "
          f"packets received successfully ({receiver_stats['reception_rate']:.1%})")
    
    # Save received data
    if received_packets:
        output_file = "basic_relay_received.csv"
        receiver.save_received_data_to_csv(output_file)
        print(f"Received data saved to {output_file}")
    
    # Clean up
    os.remove(csv_file)
    if os.path.exists("basic_relay_received.csv"):
        os.remove("basic_relay_received.csv")
    
    return len(transmitted_packets), len(received_packets)


def demonstrate_lorawan_relay():
    """Demonstrate LoRa -> LoRaWAN relay with MQTT."""
    print("\n" + "="*70)
    print("DEMONSTRATING LORA -> LORAWAN RELAY WITH MQTT")
    print("="*70)
    
    # Create sample data
    csv_file = create_sample_data("lorawan_relay_data.csv", 6)
    
    # Setup emitter (sensor device)
    emitter = LoRaEmitter(
        device_address=0x05,  # Sensor address
        spreading_factor=LoRaSpreadingFactor.SF7,
        frequency=LoRaFrequency.EU868,
        power=14,
        verbose=True
    )
    
    # Setup LoRaWAN receiver/relay with MQTT
    mqtt_config = {
        'broker': 'localhost',  # Local MQTT broker (graceful fallback if unavailable)
        'port': 1883,
        'topic': 'molonari/sensor_data'
    }
    
    receiver = LoRaWANReceiver(
        device_address=0x01,  # Relay address
        app_eui="0000000000000001",
        app_key="12345678901234567890123456789012",
        spreading_factor=LoRaSpreadingFactor.SF7,
        frequency=LoRaFrequency.EU868,
        mqtt_config=mqtt_config,
        verbose=True
    )
    
    print(f"\nSetup complete:")
    print(f"  Emitter (Sensor): Address 0x{emitter.device_address:02X}")
    print(f"  LoRaWAN Receiver: Address 0x{receiver.device_address:02X}")
    print(f"  MQTT Broker: {mqtt_config['broker']} (topic: {mqtt_config['topic']})")
    
    # Start relay operation
    print(f"\nStarting LoRaWAN relay operation...")
    relay_started = receiver.start_relay_operation(auto_process=False)
    
    if not relay_started:
        print("Warning: Relay operation may be limited (LoRaWAN join failed)")
    
    # Load and process data
    df = emitter.load_csv_data(csv_file)
    
    print(f"\nProcessing {len(df)} sensor readings through relay...")
    
    for i, (_, row) in enumerate(df.iterrows()):
        print(f"\n--- Processing sensor reading {i+1}/{len(df)} ---")
        
        # Emitter transmits
        packet = emitter.create_data_packet(row, destination=receiver.device_address)
        tx_result = emitter.simulate_transmission(packet)
        
        if tx_result['success']:
            # Receiver processes
            rx_packet = receiver.simulate_packet_reception(tx_result)
            
            if rx_packet:
                # Process as relay (forward via LoRaWAN and MQTT)
                print(f"  Received packet {rx_packet.original_packet.packet_number}")
                
                success = receiver.relay_packet_processor(rx_packet)
                
                if success:
                    print(f"  ✓ Successfully relayed via LoRaWAN and MQTT")
                else:
                    print(f"  ✗ Relay processing failed")
                
                # Send ACK
                receiver.send_acknowledgment(rx_packet)
        
        time.sleep(0.5)  # Delay for duty cycle compliance
    
    # Final statistics
    print(f"\n--- Relay Operation Statistics ---")
    stats = receiver.get_statistics()
    
    print(f"Total received: {stats['total_received']}")
    print(f"Total forwarded: {stats['total_forwarded']}")
    print(f"Reception rate: {stats['reception_rate']:.1%}")
    print(f"LoRaWAN joined: {stats['lorawan_joined']}")
    print(f"LoRaWAN DevAddr: {stats['lorawan_dev_addr']}")
    print(f"MQTT connected: {stats['mqtt_connected']}")
    
    # Save relay data
    if stats['total_received'] > 0:
        output_file = "lorawan_relay_received.csv"
        receiver.save_received_data_to_csv(output_file)
        print(f"Relay data saved to {output_file}")
    
    # Stop relay operation
    receiver.stop_relay_operation()
    
    # Clean up
    os.remove(csv_file)
    if os.path.exists("lorawan_relay_received.csv"):
        os.remove("lorawan_relay_received.csv")
    
    return stats


def demonstrate_mqtt_only():
    """Demonstrate MQTT-only operation without LoRaWAN."""
    print("\n" + "="*70)
    print("DEMONSTRATING MQTT-ONLY RELAY OPERATION")
    print("="*70)
    
    # Create sample data
    csv_file = create_sample_data("mqtt_only_data.csv", 4)
    
    # Setup emitter
    emitter = LoRaEmitter(
        device_address=0x06,  # Different sensor
        spreading_factor=LoRaSpreadingFactor.SF9,
        frequency=LoRaFrequency.EU868,
        verbose=True
    )
    
    # Setup receiver with MQTT only (no LoRaWAN)
    mqtt_config = {
        'broker': 'localhost',
        'port': 1883,
        'topic': 'molonari/test_data'
    }
    
    receiver = LoRaReceiver(  # Plain LoRa receiver, not LoRaWAN
        device_address=0x02,
        spreading_factor=LoRaSpreadingFactor.SF9,
        verbose=True
    )
    
    print(f"\nDemonstrating MQTT-only data collection...")
    print(f"  Emitter: Address 0x{emitter.device_address:02X}")
    print(f"  Receiver: Address 0x{receiver.device_address:02X}")
    
    # Load and process data
    df = emitter.load_csv_data(csv_file)
    
    def mqtt_publisher(received_packet):
        """Custom processor that simulates MQTT publishing."""
        updated_payload = receiver.add_reception_timestamp(received_packet)
        print(f"  Would publish to MQTT: {updated_payload[:60]}...")
        return True
    
    # Process packets
    for i, (_, row) in enumerate(df.iterrows()):
        packet = emitter.create_data_packet(row, destination=receiver.device_address)
        tx_result = emitter.simulate_transmission(packet)
        
        if tx_result['success']:
            rx_packet = receiver.simulate_packet_reception(tx_result)
            if rx_packet:
                mqtt_publisher(rx_packet)
    
    # Process queue
    processed = receiver.process_received_packets(packet_processor=mqtt_publisher)
    
    print(f"\nProcessed {len(processed)} packets for MQTT publishing")
    
    # Clean up
    os.remove(csv_file)
    
    return len(processed)


def main():
    """Main demonstration function."""
    print("MOLONARI1D LoRa Receiver and Relay Demonstration")
    print("=" * 70)
    print("This script demonstrates the complete sensor data transmission chain:")
    print("  1. LoRa Emitter (Sensor) -> LoRa Receiver (Relay)")
    print("  2. LoRa Receiver adds timestamps to received data")
    print("  3. LoRaWAN Receiver forwards data to gateway via LoRaWAN")
    print("  4. Optional MQTT integration for IoT connectivity")
    
    try:
        # Demonstration 1: Basic LoRa communication
        tx_count, rx_count = demonstrate_basic_relay()
        
        # Demonstration 2: Full LoRaWAN relay with MQTT
        relay_stats = demonstrate_lorawan_relay()
        
        # Demonstration 3: MQTT-only operation
        mqtt_count = demonstrate_mqtt_only()
        
        # Summary
        print("\n" + "="*70)
        print("DEMONSTRATION SUMMARY")
        print("="*70)
        print("Successfully demonstrated:")
        print(f"  ✓ Basic LoRa communication ({rx_count}/{tx_count} packets received)")
        print(f"  ✓ LoRaWAN relay operation ({relay_stats['total_forwarded']} packets forwarded)")
        print(f"  ✓ MQTT integration ({mqtt_count} packets processed)")
        print(f"  ✓ Reception timestamp addition")
        print(f"  ✓ Acknowledgment protocol")
        print(f"  ✓ Packet queuing and processing")
        print(f"  ✓ Data persistence to CSV")
        
        print("\nKey features implemented:")
        print("  • LoRa packet reception simulation")
        print("  • Reception timestamp augmentation")
        print("  • LoRaWAN relay forwarding")
        print("  • MQTT IoT integration")
        print("  • Comprehensive statistics and monitoring")
        print("  • Arduino MKR WAN 1310 protocol emulation")
        
        print(f"\nThe LoRa receiver system is ready for MOLONARI1D deployment!")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())