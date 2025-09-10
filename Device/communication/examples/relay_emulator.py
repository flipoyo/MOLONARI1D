#!/usr/bin/env python3
"""
Relay LoRa Emulator Script

This script emulates the behavior of the Arduino relay code from
Device/hardwareProgramming/Tests Codes/Relay_Lora/Relay_Lora.ino

It waits for sensor connections and receives data using the LoRa protocol
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

def print_received_data(receive_queue: list):
    """
    Print all received data from the queue
    (matches the Arduino PrintQueue function)
    """
    print("Session ended. Printing all received data:")
    for i, data in enumerate(receive_queue):
        time.sleep(0.5)  # Small delay to allow for printing
        print(f"[{i}] {data}")
    print("All data printed. Queue is now empty.")

def main():
    """Main relay emulation loop"""
    # Define the device's own address
    my_address = 0xaa
    # Default destination address (broadcast)
    default_destination = 0xff
    # Counter to rotate through test modes
    rotate = 0
    
    # Create LoRa communication object
    lora = LoRaCommunication(
        frequency=868e6,
        local_address=my_address,
        destination=default_destination,
        debug=True
    )
    
    print("Relay LoRa Emulator starting...")
    print(f"My address: 0x{my_address:02x}")
    print("Receiver ready...")
    
    session_count = 0
    
    while True:
        print(f"\n--- Waiting for sensor connection {session_count + 1} ---")
        
        # Reset destination address to default before starting
        lora.set_dest_to_default()
        
        # Queue to store received data
        receive_queue = []
        
        # Initialize LoRa communication
        if not lora.start_lora():
            print("Failed to start LoRa, retrying...")
            time.sleep(5)
            continue
        
        try:
            # Perform handshake with sensors
            if lora.perform_handshake_relay(rotate):
                print("----------- Handshake done ----------")
                
                # Receive packets and store them in the receive queue
                last_packet = lora.receive_packets(receive_queue)
                print(f"Received {len(receive_queue)} items, last packet: {last_packet}")
                
                # Close the LoRa session
                lora.close_session(last_packet)
                print("----------- Session Closed -----------")
                
                # Print all the received data
                print_received_data(receive_queue)
                
                # Increment rotation counter
                rotate += 1
                if rotate == 3:
                    rotate = 0
                
                session_count += 1
            else:
                print("Handshake failed, continuing to listen...")
        
        except KeyboardInterrupt:
            print("\nShutting down relay emulator...")
            break
        except Exception as e:
            print(f"Error in communication session: {e}")
        finally:
            # Stop LoRa communication
            lora.stop_lora()
            print("----------- LoRa Stopped ------------")
        
        # Brief pause before next session
        time.sleep(2)

if __name__ == "__main__":
    main()