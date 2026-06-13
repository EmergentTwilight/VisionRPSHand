"""
Simple servo scan test for Linux
"""
import sys
sys.path.insert(0, 'sdk_standalone')

from port_handler import PortHandler
from scscl import scscl
from stservo_def import COMM_SUCCESS

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

print("=== Scanning servos ===")
found = []
for sid in range(1, 9):
    model, result, error = ph.ping(sid)
    if result == COMM_SUCCESS:
        found.append((sid, model))
        print(f"  ✓ ID {sid}  Model={model}")

if found:
    print(f"\nFound {len(found)} servos: {[s[0] for s in found]}")
else:
    print("\n⚠️  No servos found")

portHandler.closePort()
print("🔌 Port closed")
