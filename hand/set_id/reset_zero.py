"""
reset_zero.py - 所有舵机恢复零位

功能: 将 8 个 SC09 舵机(ID 1~8)恢复到机械零位(位置 512)
      用于调试或机械调整前复位。

用法:
  python reset_zero.py             # 回到 512 机械零位
  python reset_zero.py --middle    # 回到 MiddlePos 校准位置
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stservo.sdk import *

PORT = "COM13"
BAUDRATE = 1000000

# AmazingHand MiddlePos 校准值 (仅 --middle 模式使用)
# 替换为你 calibrate 的结果
MiddlePos = [116.0, -109.0, 0.7, -0.7, 27.8, -31.3, 0.7, -31.8]


def deg_to_raw(deg):
    """角度 -> SC09 10-bit 原始位置 (512 = 0度)"""
    raw = int(512 + deg * 1024 / 360)
    return max(0, min(1023, raw))


def main():
    use_middle = len(sys.argv) > 1 and sys.argv[1] == "--middle"

    portHandler = PortHandler(PORT)
    if not portHandler.openPort():
        print(f"Error: 无法打开串口 {PORT}")
        return
    if not portHandler.setBaudRate(BAUDRATE):
        print("Error: 无法设置波特率")
        portHandler.closePort()
        return
    print(f"串口 {PORT} 已打开\n")

    ph = scscl(portHandler)

    # 扫描在线舵机
    ids = []
    for sid in range(1, 9):
        model, result, error = ph.ping(sid)
        if result == COMM_SUCCESS:
            ids.append(sid)
            print(f"  [OK] ID {sid}  在线")
        else:
            print(f"  [!!] ID {sid}  无响应")

    if not ids:
        print("\n没有找到任何舵机")
        portHandler.closePort()
        return

    # 确定目标位置
    if use_middle:
        print(f"\n目标: MiddlePos 校准位置 (角度)")
        targets = {}
        for i, sid in enumerate(ids):
            targets[sid] = deg_to_raw(MiddlePos[i])
            print(f"   ID {sid} -> {MiddlePos[i]:+.1f} deg (raw={targets[sid]})")
    else:
        print(f"\n目标: 机械零位 512")
        targets = {sid: 512 for sid in ids}

    input("\n按 Enter 开始复位...")

    # 使能扭矩
    print("\n使能扭矩...")
    for sid in ids:
        ph.write1ByteTxRx(sid, 40, 1)
    time.sleep(0.2)

    # 逐个转到目标位置
    print("\n移动中...")
    for sid in ids:
        pos_before, _, _ = ph.ReadPos(sid)
        target = targets[sid]
        ph.WritePos(sid, target, 1500, 300)
        print(f"  ID {sid}: {pos_before:4d} -> {target:4d}")
        time.sleep(0.3)

    # 等待到位
    print("\n等待到位...")
    time.sleep(2.5)

    # 验证
    print("\n=== 验证 ===")
    all_ok = True
    for sid in ids:
        pos, _, _ = ph.ReadPos(sid)
        target = targets[sid]
        ok = abs(pos - target) < 10
        if not ok:
            all_ok = False
        status = "[OK]" if ok else "[!!]"
        print(f"  ID {sid}: {pos:4d}  {status}  (目标 {target})")

    if all_ok:
        print("\n全部到位，扭矩已使能，舵机保持位置")
        print("调整完成后按 Ctrl+C 退出")
    else:
        print("\n部分舵机未到位")

    # 保持扭矩，等用户退出
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n禁用扭矩...")
        for sid in ids:
            ph.write1ByteTxRx(sid, 40, 0)
        portHandler.closePort()
        print("完成")


if __name__ == "__main__":
    main()
