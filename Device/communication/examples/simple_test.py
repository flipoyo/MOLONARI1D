#!/usr/bin/env python3
"""
Simple Test Script for LoRa Communication Emulation

This script demonstrates basic functionality of the LoRa protocol emulation
using the high-level sensor and relay emulator classes.
"""

import time
import logging
import threading
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from Device.communication.lora_emulation import LoRaSensorEmulator, LoRaRelayEmulator

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_sensor():
    """Test sensor functionality"""
    print("Starting sensor test...")
    
    sensor = LoRaSensorEmulator(
        local_address=0xcc,
        relay_address=0xaa,
        debug=True
    )
    
    # Generate test data
    test_data = [
        "2024-11-07,10:00:12,21.55,22.11,21.99,21",
        "2024-11-07,10:00:27,21.56,22.12,22.00,22",
        "2024-11-07,10:00:42,21.57,22.13,22.01,23",
        "Hello from sensor test",
        "Final test message"
    ]
    
    # Wait a moment for relay to start
    time.sleep(2)
    
    # Send data session
    success = sensor.send_data_session(test_data)
    print(f"Sensor session result: {'SUCCESS' if success else 'FAILED'}")

def test_relay():
    """Test relay functionality"""
    print("Starting relay test...")
    
    relay = LoRaRelayEmulator(
        local_address=0xaa,
        debug=True
    )
    
    # Receive data session
    received_data = relay.receive_data_session(shift_back=5)
    
    if received_data:
        print(f"Relay received {len(received_data)} items:")
        for i, item in enumerate(received_data):
            print(f"  [{i}] {item}")
    else:
        print("Relay session failed")

def main():
    """Run a simple test of sensor-relay communication"""
    print("LoRa Communication Protocol Test")
    print("=" * 40)
    
    try:
        # Start relay in a separate thread
        relay_thread = threading.Thread(target=test_relay, daemon=True)
        relay_thread.start()
        
        # Start sensor after a short delay
        time.sleep(1)
        test_sensor()
        
        # Wait for relay to complete
        relay_thread.join(timeout=30)
        
        print("\nTest completed!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    main()