"""
test_move.py - 让 SCS 舵机小范围动一下
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stservo.sdk import *

PORT = "COM13"
BAUDRATE = 1000000
SERVO_ID = 1

portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ 无法打开串口 {PORT}")
    exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ 无法设置波特率")
    exit(1)
print(f"✅ 串口 {PORT} 已打开\n")

ph = scscl(portHandler)

model, result, error = ph.ping(SERVO_ID)
if result != COMM_SUCCESS:
    print(f"❌ 舵机 ID={SERVO_ID} 无响应")
    portHandler.closePort()
    exit(1)
print(f"✅ 发现舵机 ID={SERVO_ID}  Model={model}")

# 使能扭矩
print("\n1️⃣ 使能扭矩")
ph.write1ByteTxRx(SERVO_ID, 40, 1)
time.sleep(0.2)

# 读当前位置
pos, _, _ = ph.ReadPos(SERVO_ID)
print(f"2️⃣ 当前位置: {pos}")

# 移动 +100
target = min(pos + 100, 4095)
print(f"3️⃣ 移动到 {target}")
ph.WritePos(SERVO_ID, target, 1000, 500)
time.sleep(2)

pos2, _, _ = ph.ReadPos(SERVO_ID)
print(f"4️⃣ 到达: {pos2}")

# 回原位
print(f"5️⃣ 回到 {pos}")
ph.WritePos(SERVO_ID, pos, 1000, 500)
time.sleep(2)

# 禁用扭矩
print("6️⃣ 禁用扭矩")
ph.write1ByteTxRx(SERVO_ID, 40, 0)

portHandler.closePort()
print("\n✅ 完成")
