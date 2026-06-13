"""
scan_servo_id.py - 扫描所有 SCS/CL 舵机 ID
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stservo.sdk import *

PORT = "COM13"
BAUDRATE = 1000000

portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ 无法打开串口 {PORT}")
    exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ 无法设置波特率")
    exit(1)
print(f"✅ 串口 {PORT} 已打开\n")

ph = scscl(portHandler)

print("=== 扫描舵机中 ===")
found = []
for sid in range(254):
    model, result, error = ph.ping(sid)
    if result == COMM_SUCCESS:
        found.append((sid, model))
        print(f"  ✓ ID {sid:3d}  Model={model}")

if found:
    print(f"\n共发现 {len(found)} 个舵机: {[s[0] for s in found]}")
else:
    print("\n⚠️  没有找到任何舵机")

portHandler.closePort()
print("🔌 串口已关闭")
