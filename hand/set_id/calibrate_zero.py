"""
calibrate_zero.py - 将 8 个 SC09 舵机转到零位（中心位置 512），以便机械连接
SC09 是 10 位舵机，范围 0~1023，零位 = 512
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stservo.sdk import *

PORT = "COM13"
BAUDRATE = 1000000
IDS = [1, 2]
CENTER = 512  # SC09 是 10 位，范围 0~1023，中点 = 512

portHandler = PortHandler(PORT)
if not portHandler.openPort():
    print(f"❌ 无法打开串口 {PORT}")
    exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ 无法设置波特率")
    exit(1)
print(f"✅ 串口 {PORT} 已打开\n")

ph = scscl(portHandler)

# 确认所有舵机在线
print("=== 确认舵机在线 ===")
for sid in IDS:
    model, result, error = ph.ping(sid)
    if result == COMM_SUCCESS:
        print(f"  ✓ ID {sid}  Model={model}")
    else:
        print(f"  ❌ ID {sid} 无响应")

print(f"\n即将把所有舵机转到零位（位置 {CENTER}）")
print("请准备好舵机臂/机械连接件")
input("按 Enter 开始转动...\n")

# 先使能所有舵机的扭矩
print("使能扭矩...")
for sid in IDS:
    ph.write1ByteTxRx(sid, 40, 1)
time.sleep(0.2)

# 逐个转到零位
for sid in IDS:
    pos_before, _, _ = ph.ReadPos(sid)
    print(f"  ID {sid}: {pos_before} → {CENTER}")
    ph.WritePos(sid, CENTER, 1500, 300)  # 时间 1500，速度 300
    time.sleep(0.5)

# 等待全部到位
print("\n等待舵机到位...")
time.sleep(3)

# 验证位置
print("\n=== 验证位置 ===")
all_ok = True
for sid in IDS:
    pos, result, _ = ph.ReadPos(sid)
    ok = abs(pos - CENTER) < 10
    status = "✅" if ok else "⚠️"
    if not ok:
        all_ok = False
    print(f"  ID {sid}: {pos}  {status}")

if all_ok:
    print("\n所有舵机已到零位！现在可以机械连接了")
    print("⚠️ 扭矩已使能，舵机会保持在零位不动")
    print("   装好机械结构后，按 Ctrl+C 退出或重启舵机电源即可")
else:
    print("\n⚠️ 部分舵机可能未到位")

# 保持扭矩，等用户手动退出
try:
    print("\n保持位置中（扭矩已使能），按 Ctrl+C 退出...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n用户中断，禁用扭矩...")
    for sid in IDS:
        ph.write1ByteTxRx(sid, 40, 0)
    portHandler.closePort()
    print("🔌 完成")
