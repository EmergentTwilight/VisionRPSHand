#!/usr/bin/env python
#
# *********     Torque Control Example      *********
#

import sys
import os
import time

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
STS_ID = 1
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

print("\nTorque Control Example")
print("Press 'e' to enable torque, 'd' to disable torque, ESC to quit")

while True:
    key = getch()
    
    if key == chr(0x1b):  # ESC
        print("Exiting...")
        break
    elif key.lower() == 'e':
        print("Enabling torque...")
        sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE, 1)
        if sts_comm_result != COMM_SUCCESS:
            print("Failed to enable torque")
        elif sts_error != 0:
            print("STServo error: %d" % sts_error)
        else:
            print("✓ Torque enabled")
    elif key.lower() == 'd':
        print("Disabling torque...")
        sts_comm_result, sts_error = packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE, 0)
        if sts_comm_result != COMM_SUCCESS:
            print("Failed to disable torque")
        elif sts_error != 0:
            print("STServo error: %d" % sts_error)
        else:
            print("✓ Torque disabled")
    else:
        print("Invalid key! Use 'e' to enable, 'd' to disable, ESC to quit")

# Ensure torque is disabled before exit
packetHandler.write1ByteTxRx(STS_ID, STS_TORQUE_ENABLE, 0)
portHandler.closePort()
