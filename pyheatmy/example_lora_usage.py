#!/usr/bin/env python3
"""
Example usage of LoRa and LoRaWAN emitters for MOLONARI1D sensor data.

This script demonstrates how to use the LoRaEmitter and LoRaWANEmitter classes
to simulate transmission of sensor data from CSV files.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the pyheatmy package to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyheatmy.lora_emitter import (
    LoRaEmitter, LoRaWANEmitter, LoRaPacket,
    LoRaSpreadingFactor, LoRaFrequency
)


def create_sample_data(filename="sample_sensor_data.csv", num_records=20):
    """
    Create sample sensor data similar to MOLONARI1D format.
    
    Parameters:
    -----------
    filename : str
        Output CSV filename
    num_records : int
        Number of data records to generate
    """
    print(f"Creating sample data with {num_records} records...")
    
    # Generate timestamps (15-minute intervals)
    start_time = datetime.now() - timedelta(hours=num_records * 0.25)
    timestamps = [start_time + timedelta(minutes=15*i) for i in range(num_records)]
    
    # Generate realistic temperature data (seasonal variation + daily cycle)
    base_temp = 15.0  # Base temperature in Celsius
    daily_variation = 5.0
    seasonal_offset = 0.0
    noise_level = 0.5
    
    temperatures = []
    for i, ts in enumerate(timestamps):
        # Daily cycle
        hour_angle = (ts.hour + ts.minute/60) * 2 * np.pi / 24
        daily_temp = base_temp + daily_variation * np.sin(hour_angle - np.pi/2)
        
        # Add noise
        temp = daily_temp + np.random.normal(0, noise_level)
        temperatures.append(round(temp, 2))
    
    # Generate pressure data (more stable)
    base_pressure = 1013.25  # Standard atmospheric pressure
    pressures = [round(base_pressure + np.random.normal(0, 2.0), 2) for _ in range(num_records)]
    
    # Create DataFrame
    data = pd.DataFrame({
        'Date Heure, GMT+01:00': [ts.strftime('%m/%d/%y %I:%M:%S %p') for ts in timestamps],
        'Temp_1': temperatures,
        'Temp_2': [t + np.random.normal(0, 0.3) for t in temperatures],
        'Temp_3': [t + np.random.normal(0, 0.3) for t in temperatures],
        'Temp_4': [t + np.random.normal(0, 0.3) for t in temperatures],
        'Pressure': pressures
    })
    
    # Round temperature columns
    for col in ['Temp_2', 'Temp_3', 'Temp_4']:
        data[col] = data[col].round(2)
    
    data.to_csv(filename, index=False)
    print(f"Sample data saved to {filename}")
    return filename


def demonstrate_lora_emitter():
    """Demonstrate basic LoRa emitter functionality."""
    print("\n" + "="*60)
    print("DEMONSTRATING LORA EMITTER")
    print("="*60)
    
    # Create sample data
    csv_file = create_sample_data("lora_sample_data.csv", 10)
    
    # Initialize LoRa emitter
    emitter = LoRaEmitter(
        device_address=0x05,  # Sensor address (like in Arduino code)
        spreading_factor=LoRaSpreadingFactor.SF7,  # Good for short range, high data rate
        frequency=LoRaFrequency.EU868,  # European frequency band
        power=14,  # dBm
        max_retries=6,  # As specified in documentation
        verbose=True
    )
    
    print(f"\nInitialized LoRa emitter with address 0x{emitter.device_address:02X}")
    print(f"Spreading Factor: SF{emitter.spreading_factor.sf}")
    print(f"Frequency: {emitter.frequency.value} MHz")
    print(f"Transmission Power: {emitter.power} dBm")
    
    # Emit data
    print(f"\nEmitting data from {csv_file}...")
    results = emitter.emit_csv_data(
        csv_file,
        destination=0x01,  # Relay address
        transmission_interval=0.5  # 500ms between transmissions
    )
    
    # Display results
    print(f"\nTransmission completed!")
    print(f"Total packets sent: {len(results)}")
    
    stats = emitter.get_statistics()
    print(f"\nStatistics:")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Average airtime: {stats['average_airtime_ms']:.1f} ms")
    print(f"  Average retries: {stats['average_retries']:.1f}")
    
    # Show some example packets
    print(f"\nExample transmitted packets:")
    for i, result in enumerate(results[:3]):
        packet = result['packet']
        print(f"  Packet {i+1}: {packet.payload[:50]}..." if len(packet.payload) > 50 else f"  Packet {i+1}: {packet.payload}")
        print(f"    Size: {packet.get_size()} bytes, Airtime: {result['airtime_ms']:.1f}ms, Success: {result['success']}")
    
    # Clean up
    os.remove(csv_file)


def demonstrate_lorawan_emitter():
    """Demonstrate LoRaWAN emitter with network features."""
    print("\n" + "="*60)
    print("DEMONSTRATING LORAWAN EMITTER")
    print("="*60)
    
    # Create sample data
    csv_file = create_sample_data("lorawan_sample_data.csv", 15)
    
    # Initialize LoRaWAN emitter
    emitter = LoRaWANEmitter(
        device_address=0x10,  # Different address for LoRaWAN device
        app_eui="0000000000000000",  # Application EUI
        app_key="387BC5DEF778168781DDE361D4407953",  # Application Key
        spreading_factor=LoRaSpreadingFactor.SF10,  # Higher SF for better reliability
        duty_cycle_limit=0.01,  # 1% duty cycle limit (EU regulation)
        verbose=True
    )
    
    print(f"\nInitialized LoRaWAN emitter with DevAddr: 0x{emitter.device_address:02X}")
    print(f"AppEUI: {emitter.app_eui}")
    print(f"Duty cycle limit: {emitter.duty_cycle_limit*100:.1f}%")
    
    # Join network (simulate OTAA)
    print(f"\nAttempting to join LoRaWAN network...")
    if emitter.join_network(max_attempts=3):
        print(f"Successfully joined network!")
        print(f"Device Address: {emitter.dev_addr}")
        
        # Emit data over LoRaWAN
        print(f"\nEmitting data over LoRaWAN...")
        results = emitter.emit_csv_data_lorawan(
            csv_file,
            transmission_interval=2.0  # Longer interval for duty cycle compliance
        )
        
        # Display results
        print(f"\nLoRaWAN transmission completed!")
        
        stats = emitter.get_statistics()
        print(f"\nLoRaWAN Statistics:")
        print(f"  Join status: {'Joined' if stats['is_joined'] else 'Not joined'}")
        print(f"  Device address: {stats['dev_addr']}")
        print(f"  Total packets: {stats['total_packets']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Current duty cycle: {stats['current_duty_cycle']*100:.3f}%")
        print(f"  Transmissions last hour: {stats['transmissions_last_hour']}")
        
        # Show example LoRaWAN packets
        if results:
            print(f"\nExample LoRaWAN packets:")
            for i, result in enumerate(results[:3]):
                if result['success']:
                    packet = result['packet']
                    print(f"  Frame {i+1}: FCnt={result.get('fcnt', 'N/A')}, DevAddr={result.get('dev_addr', 'N/A')}")
                    print(f"    Payload: {packet.payload[:40]}...")
                    print(f"    Confirmed: {result.get('confirmed', False)}")
        
    else:
        print("Failed to join LoRaWAN network. This is normal in simulation.")
        print("In a real deployment, check network coverage and credentials.")
    
    # Clean up
    os.remove(csv_file)


def demonstrate_packet_structure():
    """Demonstrate the LoRa packet structure."""
    print("\n" + "="*60)
    print("DEMONSTRATING PACKET STRUCTURE")
    print("="*60)
    
    # Create a sample packet similar to Arduino format
    packet = LoRaPacket(
        checksum=0x00,  # Will be calculated
        destination=0x01,  # Relay address
        local_address=0x05,  # Sensor address  
        packet_number=42,
        request_type=0xc3,  # Data transfer request
        payload="2024-11-07,10:00:12,21.55,22.11,21.99,21.30,1013.25",
        timestamp=datetime.now()
    )
    
    # Calculate checksum
    packet.checksum = packet.calculate_checksum()
    
    print("LoRa Packet Structure (as used in MOLONARI1D):")
    print(f"  Checksum: 0x{packet.checksum:02X} ({packet.checksum})")
    print(f"  Destination: 0x{packet.destination:02X} ({packet.destination})")
    print(f"  Local Address: 0x{packet.local_address:02X} ({packet.local_address})")
    print(f"  Packet Number: 0x{packet.packet_number:02X} ({packet.packet_number})")
    print(f"  Request Type: 0x{packet.request_type:02X} ({packet.request_type})")
    print(f"  Payload: '{packet.payload}'")
    print(f"  Total Size: {packet.get_size()} bytes")
    
    # Show byte representation
    packet_bytes = packet.to_bytes()
    hex_repr = ' '.join(f'{b:02X}' for b in packet_bytes[:10])
    if len(packet_bytes) > 10:
        hex_repr += f" ... ({len(packet_bytes)} bytes total)"
    
    print(f"  Byte representation: {hex_repr}")
    
    # Show spreading factor comparison
    print(f"\nSpreading Factor Comparison:")
    for sf in LoRaSpreadingFactor:
        airtime_approx = packet.get_size() * 8 / sf.bitrate * 1000  # Approximate airtime in ms
        print(f"  {sf.name}: {sf.bitrate} bps, ~{airtime_approx:.1f}ms airtime")


def main():
    """Main demonstration function."""
    print("MOLONARI1D LoRa/LoRaWAN Emitter Demonstration")
    print("=" * 60)
    print("This script demonstrates the LoRa and LoRaWAN emitter classes")
    print("for simulating sensor data transmission from CSV files.")
    
    try:
        # Demonstrate packet structure
        demonstrate_packet_structure()
        
        # Demonstrate basic LoRa emission
        demonstrate_lora_emitter()
        
        # Demonstrate LoRaWAN emission
        demonstrate_lorawan_emitter()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("The LoRa/LoRaWAN emitter classes are ready for use!")
        print("\nKey features demonstrated:")
        print("  ✓ CSV data loading and processing")
        print("  ✓ LoRa packet creation and formatting")
        print("  ✓ Transmission simulation with realistic timing")
        print("  ✓ Retry mechanism with exponential backoff")
        print("  ✓ LoRaWAN join procedure (OTAA)")
        print("  ✓ Duty cycle compliance checking")
        print("  ✓ Comprehensive statistics and monitoring")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())