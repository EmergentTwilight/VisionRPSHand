"""
AmazingHand RPS Gestures Demo
Rock/Paper/Scissors gestures
"""
import sys
sys.path.insert(0, 'sdk_standalone')
import time

from port_handler import PortHandler
from scscl import scscl, SCSCL_TORQUE_ENABLE
from stservo_def import *

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

print(f"🦾 AmazingHand Gesture Demo")
print(f"Opening port {PORT}...")

portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ Cannot open port {PORT}")
    exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Cannot set baudrate")
    exit(1)
print(f"✅ Port opened\n")

ph = scscl(portHandler)

# Enable torque for all servos
print("Enabling torque...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 1)
time.sleep(0.3)

# Gesture positions (8 servos, 2 per finger)
# Finger mapping: index(1,2), middle(3,4), ring(5,6), thumb(7,8)
GESTURES = {
    'rock':     [300, 700, 300, 700, 300, 700, 300, 700],  # Fist
    'paper':    [700, 300, 700, 300, 700, 300, 700, 300],  # Open
    'scissors': [300, 700, 700, 300, 700, 300, 300, 700],  # Index+Middle open, others closed
}

def make_gesture(name):
    """Make a gesture"""
    positions = GESTURES[name]
    for i, sid in enumerate(range(1, 9)):
        ph.WritePos(sid, positions[i], 0, 50)

try:
    while True:
        print("\n" + "="*50)
        print("✊ Rock (fist)")
        make_gesture('rock')
        time.sleep(2)
        
        print("\n🖐️ Paper (open)")
        make_gesture('paper')
        time.sleep(2)
        
        print("\n✌️ Scissors")
        make_gesture('scissors')
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\n⏹ Interrupted")

finally:
    print("🔌 Disabling torque...")
    for sid in range(1, 9):
        ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 0)
    portHandler.closePort()
    print("✅ Done")
