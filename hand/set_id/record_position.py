"""
record_position.py - 手动调整并记录舵机位置

流程:
  1. 读取 8 个舵机当前位置 (起始位置)
  2. 放开扭矩，让你手动调整手指姿态
  3. 按 Enter 停止调整，重新使能扭矩
  4. 读取 8 个舵机新位置 (结束位置)
  5. 计算并显示每个舵机的前后变化量
  6. 将结果保存到文件

用法:
  python record_position.py
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stservo.sdk import *

PORT = "COM13"
BAUDRATE = 1000000

portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ 无法打开串口 {PORT}")
    exit(1)
portHandler.setBaudRate(BAUDRATE)

ph = scscl(portHandler)

# 使能扭矩
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, 40, 1)
time.sleep(0.2)

# 读取起始位置
print("读取起始位置...")
start_pos = {}
for sid in range(1, 9):
    pos, result, error = ph.ReadPos(sid)
    start_pos[sid] = pos if result == COMM_SUCCESS else -1
    print(f"  ID {sid}: {pos}")

# 放开扭矩
print("\n已放开扭矩，请手动调整手指姿态")
print("调整完成后按 Enter 继续...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, 40, 0)
input()

# 重新使能扭矩并读取结束位置
print("\n重新使能扭矩，读取结束位置...")
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, 40, 1)
time.sleep(0.3)

end_pos = {}
for sid in range(1, 9):
    pos, result, error = ph.ReadPos(sid)
    end_pos[sid] = pos if result == COMM_SUCCESS else -1
    print(f"  ID {sid}: {pos}")

# 计算差值
print("\n变化量:")
for sid in range(1, 9):
    delta = end_pos[sid] - start_pos[sid]
    print(f"  ID {sid}: {start_pos[sid]} -> {end_pos[sid]}  ({delta:+d})")

# 保存到文件
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"position_record_{timestamp}.txt"
with open(filename, "w", encoding="utf-8") as f:
    f.write(f"Position Record - {datetime.now()}\n")
    f.write(f"{'ID':<5} {'Start':<8} {'End':<8} {'Delta':<8}\n")
    f.write("-" * 32 + "\n")
    for sid in range(1, 9):
        delta = end_pos[sid] - start_pos[sid]
        f.write(f"{sid:<5} {start_pos[sid]:<8} {end_pos[sid]:<8} {delta:+d}\n")

print(f"\n✅ 结果已保存到 {filename}")

# 禁用扭矩
for sid in range(1, 9):
    ph.write1ByteTxRx(sid, 40, 0)
portHandler.closePort()
