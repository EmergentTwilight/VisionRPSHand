"""
AmazingHand Rock-Paper-Scissors Gestures Demo
Based on finger mapping from README:
- Index (食指): ID 1, 2
- Middle (中指): ID 3, 4  
- Ring (无名指): ID 5, 6
- Thumb (拇指): ID 7, 8
"""
import sys
sys.path.insert(0, 'sdk_standalone')
import time

from port_handler import PortHandler
from scscl import scscl, SCSCL_TORQUE_ENABLE
from stservo_def import *

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

print(f"🦾 AmazingHand RPS Gestures Demo")
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

# Position ranges (0-1023, 512 is center):
# Lower value = curl in, Higher value = extend out
# Each finger has 2 servos - they move in opposite directions

# RPS Gestures
# Rock: All fingers closed (fist)
# Paper: All fingers open  
# Scissors: Index+Middle open, Ring+Thumb closed

GESTURES = {
    'rock': [350, 650, 350, 650, 350, 650, 350, 650],     # ✊ Fist - all closed
    'paper': [650, 350, 650, 350, 650, 350, 650, 350],    # 🖐️ Open - all extended
    'scissors': [650, 350, 650, 350, 350, 650, 350, 650], # ✌️ Index+Middle open, Ring+Thumb closed
}

GESTURE_NAMES = {
    'rock': '✊ 石头 (Rock)',
    'paper': '🖐️ 布 (Paper)', 
    'scissors': '✌️ 剪刀 (Scissors)'
}

def make_gesture(name):
    """Make a gesture - send position commands to all 8 servos"""
    positions = GESTURES[name]
    for i, sid in enumerate(range(1, 9)):
        ph.WritePos(sid+1, positions[i], 0, 60)  # position, time, speed

print("Enabling torque for all servos (IDs 1-8)...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 1)
time.sleep(0.3)

print("\nFinger mapping:")
print("  食指 (Index):   Servo 1, 2")
print("  中指 (Middle):  Servo 3, 4")
print("  无名指 (Ring):  Servo 5, 6")
print("  拇指 (Thumb):   Servo 7, 8")
print()

try:
    while True:
        for gesture in ['rock', 'paper', 'scissors']:
            print(f"\n{'='*50}")
            print(f"Showing: {GESTURE_NAMES[gesture]}")
            make_gesture(gesture)
            time.sleep(2.5)
        
except KeyboardInterrupt:
    print("\n\n⏹ Demo stopped by user")

finally:
    print("🔌 Disabling torque...")
    for sid in range(1, 9):
        ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 0)
    portHandler.closePort()
    print("✅ Done")
