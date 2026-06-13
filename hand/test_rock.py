"""
AmazingHand - Rock Gesture Test
"""
import sys
sys.path.insert(0, 'sdk_standalone')
import time

from port_handler import PortHandler
from scscl import scscl, SCSCL_TORQUE_ENABLE
from stservo_def import *

PORT = "/dev/ttyACM0"
BAUDRATE = 1000000

print(f"🦾 AmazingHand - Rock Gesture")
print(f"Opening port {PORT}...")

portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ Cannot open port {PORT}")
    exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Cannot set baudrate")
    exit(1)
print(f"✅ Port opened")

ph = scscl(portHandler)

# Enable torque
print("Enabling torque...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 1)
time.sleep(0.3)

# Rock position - all fingers closed (fist)
ROCK = [350, 650, 350, 650, 350, 650, 350, 650]

print("\n✊ Making ROCK (fist)...")
for i, sid in enumerate(range(1, 9)):
    ph.WritePos(sid, ROCK[i], 0, 60)

print("Hold for 5 seconds...")
time.sleep(5)

print("🔌 Disabling torque...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, SCSCL_TORQUE_ENABLE, 0)
portHandler.closePort()
print("✅ Done")
