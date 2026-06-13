"""
read_positions.py - 读取 ID 1~8 的当前位置（SCS 协议）
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

# ⚠️ SCS/CL 舵机用 scscl，不是 sts
ph = scscl(portHandler)

print("ID | 位置 | 在线")
print("---|------|----")
for sid in range(1, 9):
    pos, result, error = ph.ReadPos(sid)
    if result == COMM_SUCCESS:
        print(f" {sid}  | {pos:4d} | ✅")
    else:
        print(f" {sid}  |  ---- | ❌")

portHandler.closePort()
