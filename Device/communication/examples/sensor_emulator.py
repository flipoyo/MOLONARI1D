#!/usr/bin/env python3
"""
Sensor LoRa Emulator Script

This script emulates the behavior of the Arduino sensor code from
Device/hardwareProgramming/Tests Codes/Sensor_Lora/Sensor_Lora.ino

It generates test data and sends it to a relay using the LoRa protocol
emulated over MQTT.
"""

import time
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from Device.communication import LoRaCommunication, RequestType

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def load_data_into_queue(shift: int = 0) -> list:
    """
    Simulate loading data into a queue for transmission
    (matches the Arduino loadDataIntoQueue function)
    """
    queue = []
    
    # Populate the queue with simulated data records
    for i in range(100 - shift, 281):
        line = f"hello from riviere{i + 1}"
        queue.append(line)
        
        # Limit queue size to 200 items for testing
        if len(queue) >= 200:
            break
    
    return queue

def main():
    """Main sensor emulation loop"""
    # Device and relay addresses for communication
    my_address = 0xcc  # Address of this device
    relay_address = 0xaa  # Address of the relay device
    
    # Create LoRa communication object
    lora = LoRaCommunication(
        frequency=868e6,
        local_address=my_address, 
        destination=relay_address,
        debug=True
    )
    
    print("Sensor LoRa Emulator starting...")
    print(f"My address: 0x{my_address:02x}")
    print(f"Relay address: 0x{relay_address:02x}")
    
    session_count = 0
    
    while True:
        print(f"\n--- Starting communication session {session_count + 1} ---")
        
        # Initialize LoRa communication
        if not lora.start_lora():
            print("Failed to start LoRa, retrying in 10 seconds...")
            time.sleep(10)
            continue
        
        try:
            shift = 0  # Variable to simulate shifting data
            
            # Perform handshake with the relay
            success, received_shift = lora.perform_handshake_sensor()
            if success:
                print(f"Handshake successful, received shift: {received_shift}")
                
                # Load data into queue after successful handshake
                send_queue = load_data_into_queue(shift)
                print(f"Loaded {len(send_queue)} data items")
                
                # Send the packets from the queue
                last_packet = lora.send_packets(send_queue)
                print(f"Sent packets, last packet number: {last_packet}")
                
                # Close the communication session with the relay
                lora.close_session(last_packet)
                print("Session closed successfully")
                
            else:
                print("Handshake failed")
        
        except KeyboardInterrupt:
            print("\nShutting down sensor emulator...")
            break
        except Exception as e:
            print(f"Error in communication session: {e}")
        finally:
            # Stop LoRa communication to save power
            lora.stop_lora()
        
        session_count += 1
        
        # Delay before starting the next session
        print("Waiting 10 seconds before next session...")
        time.sleep(10)

if __name__ == "__main__":
    main()