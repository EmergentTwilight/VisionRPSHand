#!/usr/bin/env python
#
# *********     Find Connected Servo ID      *********
#
# Simple script to quickly find the ID of a connected servo
# by checking the most commonly used ID range (0-20).
#
# Available STServo model on this example : All models using Protocol STS
# This example is tested with a STServo and an URT
#

import sys
import os
import yaml

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

sys.path.append("..")
from STservo_sdk import *                   # Uses STServo SDK library
from device_config import load_device_port, save_servo_config

# Default setting
BAUDRATE                = 1000000           # STServo default baudrate : 1000000
DEVICENAME              = load_device_port()  # Load port from YAML config

def find_connected_servo():
    """Find the first connected servo in the range 0-20"""
    
    # Initialize PortHandler instance
    portHandler = PortHandler(DEVICENAME)

    # Initialize PacketHandler instance
    packetHandler = sts(portHandler)
    
    # Open port
    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        return None

    # Set port baudrate
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        portHandler.closePort()
        return None

    print("Scanning for connected servo (ID 0-20)...")
    
    # Check most common IDs first
    common_ids = [1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    
    found_servos = []
    
    for servo_id in common_ids:
        print(f"Checking ID {servo_id}...", end=" ")
        
        # Try to ping the servo
        sts_model_number, sts_comm_result, sts_error = packetHandler.ping(servo_id)
        
        if sts_comm_result == COMM_SUCCESS and sts_error == 0:
            print(f"✓ FOUND! Model: {sts_model_number}")
            found_servos.append({
                'id': servo_id,
                'model': sts_model_number
            })
        else:
            print("✗")
    
    # Close port
    portHandler.closePort()
    
    return found_servos

def main():
    print("=" * 50)
    print("STServo ID Finder")
    print("=" * 50)
    print(f"Port: {DEVICENAME}")
    print(f"Baudrate: {BAUDRATE}")
    print("\nThis will quickly check the most common servo IDs (0-20).")
    print("Press any key to start...")
    
    getch()
    
    found_servos = find_connected_servo()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    
    if found_servos:
        print(f"Found {len(found_servos)} servo(s):")
        for servo in found_servos:
            print(f"  - ID: {servo['id']}, Model: {servo['model']}")
        
        if len(found_servos) == 1:
            servo_id = found_servos[0]['id']
            servo_model = found_servos[0]['model']
            print(f"\n✓ You can use STS_ID = {servo_id} in your code.")
            # Save the discovered servo configuration
            save_servo_config(servo_id, servo_model)
        else:
            ids = [str(servo['id']) for servo in found_servos]
            print(f"\n✓ Available servo IDs: {', '.join(ids)}")
            # Save the first found servo as default
            save_servo_config(found_servos[0]['id'], found_servos[0]['model'])
            
    else:
        print("No servos found in the common ID range (0-20).")
        print("\nTroubleshooting:")
        print("1. Check physical connections")
        print("2. Verify the servo is powered on")
        print("3. Check the port name (currently using: {})".format(DEVICENAME))
        print("4. Try running ping_smart.py for a more thorough scan")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
