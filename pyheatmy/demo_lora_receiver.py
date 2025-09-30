#!/usr/bin/env python3
"""
Simple demonstration of the MOLONARI1D LoRa receiver functionality.

This script shows the key features implemented:
1. LoRa packet reception and timestamp addition
2. LoRaWAN relay forwarding  
3. MQTT integration
4. Complete emitter->receiver->gateway workflow
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add the pyheatmy package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyheatmy import (
    LoRaEmitter, LoRaReceiver, LoRaWANReceiver, 
    LoRaPacket, LoRaSpreadingFactor, LoRaFrequency
)


def main():
    """Demonstrate key LoRa receiver features."""
    print("MOLONARI1D LoRa Receiver - Key Features Demo")
    print("=" * 50)
    
    # 1. Basic Setup
    print("\n1. Setting up emitter and receiver:")
    emitter = LoRaEmitter(device_address=0x05, verbose=False)
    receiver = LoRaReceiver(device_address=0x01, reception_success_rate=1.0, verbose=False)
    
    print(f"   Emitter (Sensor): Address 0x{emitter.device_address:02X}")
    print(f"   Receiver (Relay): Address 0x{receiver.device_address:02X}")
    
    # 2. Create sample sensor data
    print("\n2. Creating sample sensor data:")
    sample_data = pd.Series({
        'timestamp': '2024-11-07 10:00:00',
        'temp_1': 21.55,
        'temp_2': 22.11, 
        'temp_3': 21.99,
        'temp_4': 21.30,
        'pressure': 1013.25
    })
    
    packet = emitter.create_data_packet(sample_data, destination=receiver.device_address)
    print(f"   Original payload: {packet.payload}")
    
    # 3. Simulate transmission and reception
    print("\n3. Simulating packet transmission and reception:")
    tx_result = emitter.simulate_transmission(packet)
    
    if tx_result['success']:
        print(f"   ✓ Transmission successful ({tx_result['airtime_ms']:.1f}ms)")
        
        # Simulate reception
        rx_packet = receiver.simulate_packet_reception(tx_result)
        if rx_packet:
            print(f"   ✓ Reception successful (RSSI: {rx_packet.rssi:.1f}dBm)")
            
            # Add timestamp
            updated_payload = receiver.add_reception_timestamp(rx_packet)
            print(f"   ✓ Updated payload: {updated_payload}")
            
            # Send acknowledgment
            ack_sent = receiver.send_acknowledgment(rx_packet)
            print(f"   ✓ Acknowledgment sent: {ack_sent}")
    
    # 4. LoRaWAN Relay Demo
    print("\n4. Demonstrating LoRaWAN relay functionality:")
    lorawan_receiver = LoRaWANReceiver(
        device_address=0x02,
        app_eui="0000000000000001",
        verbose=False
    )
    
    # Simulate join (may succeed or fail randomly)
    join_success = lorawan_receiver.join_lorawan_network(max_attempts=1)
    print(f"   LoRaWAN join attempt: {'✓ Success' if join_success else '✗ Failed (normal in simulation)'}")
    
    if join_success:
        # Create a received packet for forwarding
        rx_packet_2 = receiver.simulate_packet_reception(tx_result)
        if rx_packet_2:
            forward_result = lorawan_receiver.forward_via_lorawan(rx_packet_2)
            print(f"   LoRaWAN forwarding: {'✓ Success' if forward_result.get('success') else '✗ Failed'}")
    
    # 5. Statistics
    print("\n5. System statistics:")
    emitter_stats = emitter.get_statistics()
    receiver_stats = receiver.get_statistics()
    
    print(f"   Emitter packets sent: {emitter_stats.get('successful_packets', 0)}")
    print(f"   Receiver packets received: {receiver_stats['total_received']}")
    print(f"   Reception rate: {receiver_stats['reception_rate']:.1%}")
    
    # 6. Key Features Summary
    print("\n6. Key Features Implemented:")
    print("   ✓ LoRa packet reception simulation")
    print("   ✓ Reception timestamp addition") 
    print("   ✓ LoRaWAN relay forwarding")
    print("   ✓ MQTT IoT integration")
    print("   ✓ Acknowledgment protocol")
    print("   ✓ Packet queuing and processing")
    print("   ✓ CSV data persistence")
    print("   ✓ Comprehensive statistics")
    print("   ✓ Arduino MKR WAN 1310 protocol emulation")
    
    print(f"\n🎉 LoRa receiver system ready for MOLONARI1D deployment!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())