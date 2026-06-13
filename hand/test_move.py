"""
Simple movement test for AmazingHand
"""
import sys
sys.path.insert(0, 'sdk_standalone')
import time

from port_handler import PortHandler
from scscl import scscl, SCSCL_TORQUE_ENABLE
from stservo_def import *

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

print(f"Opening port {PORT}...")
portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ Cannot open port {PORT}")
    exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Cannot set baudrate")
    exit(1)
print(f"✅ Port {PORT} opened\n")

ph = scscl(portHandler)

# Enable torque for all servos
print("Enabling torque...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 1)
time.sleep(0.5)

# Simple position values (0-1023, 512 is center)
FIST_POSITIONS = [300, 700, 300, 700, 300, 700, 300, 700]
OPEN_POSITIONS = [512, 512, 512, 512, 512, 512, 512, 512]

try:
    print("\n✊ Making fist...")
    for i, sid in enumerate(range(1, 9)):
        pos = FIST_POSITIONS[i]
        ph.WritePos(sid, pos, 0, 50)  # position, time, speed
    
    time.sleep(2)
    
    print("🤚 Opening hand...")
    for i, sid in enumerate(range(1, 9)):
        pos = OPEN_POSITIONS[i]
        ph.WritePos(sid, pos, 0, 50)
    
    time.sleep(2)
    
    # Read positions
    print("\n📊 Reading positions:")
    for sid in range(1, 9):
        pos, result, error = ph.ReadPos(sid)
        print(f"  Servo {sid}: {pos}")
        
except KeyboardInterrupt:
    print("\nInterrupted")

finally:
    print("\n🔌 Disabling torque...")
    for sid in range(1, 9):
        ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 0)
    portHandler.closePort()
    print("✅ Done")
