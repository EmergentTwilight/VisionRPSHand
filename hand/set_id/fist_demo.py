"""
fist_demo.py - AmazingHand 握拳测试
仅使用 rustypot Scs0009PyController，每个手指的 MiddlePos 和偏置均可独立配置
"""

import time
import numpy as np
from rustypot import Scs0009PyController


# ============================================================
# 每个手指配置
#    ids:          [servo1_id, servo2_id]
#    middle:       [servo1_middle_deg, servo2_middle_deg]
#    close_offset: [servo1, servo2]  相对 middle 的握拳偏置
#    open_offset:  [servo1, servo2]  相对 middle 的张开偏置
# ============================================================

FINGERS = {
    "index": {
        "ids":          [1, 2],
        "middle":       [0.0, 0.0],
        "close_offset": [-30, 30],
        "open_offset":  [90, -90],
    },
    "middle": {
        "ids":          [3, 4],
        "middle":       [0.0, 0.0],
        "close_offset": [-120, 120],
        "open_offset":  [30, -30],
    },
    "ring": {
        "ids":          [5, 6],
        "middle":       [0.0, 0.0],
        "close_offset": [-110, 110],
        "open_offset":  [20, -20],
    },
    "thumb": {
        "ids":          [7, 8],
        "middle":       [0.0, 0.0],
        "close_offset": [-110, 110],
        "open_offset":  [20, -20],
    },
}


# ============================================================
# 控制器
# ============================================================
c = Scs0009PyController(
    serial_port="/dev/ttyACM0",
    baudrate=1000000,
    timeout=0.5,
)


# ============================================================
# 手指动作
# ============================================================

def CloseFinger(id1, id2, mid1, mid2, off1, off2):
    c.write_goal_speed(id1, 6)
    c.write_goal_speed(id2, 6)
    pos1 = np.deg2rad(mid1 + off1)
    pos2 = np.deg2rad(mid2 + off2)
    c.write_goal_position(id1, pos1)
    c.write_goal_position(id2, pos2)
    time.sleep(0.01)


def OpenFinger(id1, id2, mid1, mid2, off1, off2):
    c.write_goal_speed(id1, 6)
    c.write_goal_speed(id2, 6)
    pos1 = np.deg2rad(mid1 + off1)
    pos2 = np.deg2rad(mid2 + off2)
    c.write_goal_position(id1, pos1)
    c.write_goal_position(id2, pos2)
    time.sleep(0.01)


def CloseHand():
    for name, cfg in FINGERS.items():
        ids = cfg["ids"]
        mid = cfg["middle"]
        off = cfg["close_offset"]
        CloseFinger(ids[0], ids[1], mid[0], mid[1], off[0], off[1])


def OpenHand():
    for name, cfg in FINGERS.items():
        ids = cfg["ids"]
        mid = cfg["middle"]
        off = cfg["open_offset"]
        OpenFinger(ids[0], ids[1], mid[0], mid[1], off[0], off[1])


# ============================================================
# 主循环
# ============================================================

def main():
    print("=" * 50)
    print("🦾 AmazingHand 握拳测试")
    print("=" * 50)

    # 使能所有舵机
    for sid in range(1, 9):
        c.write_torque_enable(sid, 1)

    # 打印当前配置
    print("\n当前配置:")
    print(f"{'手指':<8} {'IDs':<10} {'MiddlePos':<22} {'Close偏置':<18} {'Open偏置':<18}")
    print("-" * 76)
    for name, cfg in FINGERS.items():
        ids = f"{cfg['ids'][0]},{cfg['ids'][1]}"
        mid = f"{cfg['middle'][0]:.1f}, {cfg['middle'][1]:.1f}"
        cls = f"{cfg['close_offset'][0]:+.0f}, {cfg['close_offset'][1]:+.0f}"
        opn = f"{cfg['open_offset'][0]:+.0f}, {cfg['open_offset'][1]:+.0f}"
        print(f"{name:<8} {ids:<10} {mid:<22} {cls:<18} {opn:<18}")

    # input("\n⏎ 按 Enter 开始测试...")  # Auto-start for testing

    try:
        while True:
            print("\n👊 握拳...")
            CloseHand()
            time.sleep(3)

            print("🤚 张开...")
            OpenHand()
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n⏹ 用户中断")

    finally:
        print("🔌 禁用扭矩...")
        for sid in range(1, 9):
            c.write_torque_enable(sid, 2)
        print("✅ 结束")


if __name__ == "__main__":
    main()
