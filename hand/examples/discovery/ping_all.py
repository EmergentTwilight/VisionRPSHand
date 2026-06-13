#!/usr/bin/env python
#
# *********     Ping All Servos Example      *********
#

import sys
import os

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

# Import from the installed package
try:
    from stservo.sdk import *
except ImportError:
    print("Error: stservo package not installed. Please install with 'pip install -e .' from the project root")
    sys.exit(1)

# Import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config')))
try:
    from device_config import load_device_port
except ImportError:
    def load_device_port():
        return "/dev/ttyACM0"

# Default setting
BAUDRATE = 1000000
DEVICENAME = load_device_port()

# Initialize PortHandler and PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = sts(portHandler)

# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()

# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

print("\nScanning for STServos...")
print("This will ping all possible servo IDs (1-253)")
print("Found servos will be displayed below:")
print("-" * 50)

found_servos = []

# Ping all possible IDs
for servo_id in range(0, 254):  # IDs 1-253
    # Show progress
    print(f"\rScanning ID {servo_id:3d}...", end='', flush=True)
    
    model_number, comm_result, error = packetHandler.ping(servo_id)
    
    if comm_result == COMM_SUCCESS:
        found_servos.append((servo_id, model_number))
        print(f"\r✓ Found servo at ID {servo_id:3d} (Model: {model_number})")

print(f"\rScan completed!{' ' * 20}")
print("-" * 50)

if found_servos:
    print(f"Found {len(found_servos)} servo(s):")
    for servo_id, model in found_servos:
        print(f"  ID: {servo_id:3d} - Model: {model}")
else:
    print("No servos found.")
    print("\nTroubleshooting:")
    print("1. Check power connections")
    print("2. Check serial wiring (TX/RX)")
    print("3. Try different baud rates")
    print("4. Verify servo is functioning")

print("\nPress any key to exit...")
getch()
portHandler.closePort()
