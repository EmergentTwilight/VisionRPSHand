"""
wave_hello.py - 开机打招呼动画
拇指不动，其余三指依次弯曲到底后立即张开，形成波浪效果
"""

import time
import numpy as np
from rustypot import Scs0009PyController


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


c = Scs0009PyController(
    serial_port="/dev/ttyACM0",
    baudrate=1000000,
    timeout=0.5,
)


def MoveFinger(id1, id2, mid1, mid2, off1, off2):
    c.write_goal_speed(id1, 7)
    c.write_goal_speed(id2, 7)
    pos1 = np.deg2rad(mid1 + off1)
    pos2 = np.deg2rad(mid2 + off2)
    c.write_goal_position(id1, pos1)
    c.write_goal_position(id2, pos2)


def OpenFinger(name):
    cfg = FINGERS[name]
    MoveFinger(cfg["ids"][0], cfg["ids"][1],
               cfg["middle"][0], cfg["middle"][1],
               cfg["open_offset"][0], cfg["open_offset"][1])


def CloseFinger(name):
    cfg = FINGERS[name]
    MoveFinger(cfg["ids"][0], cfg["ids"][1],
               cfg["middle"][0], cfg["middle"][1],
               cfg["close_offset"][0], cfg["close_offset"][1])


def OpenAll():
    for name in FINGERS:
        OpenFinger(name)


def wave_hello(cycles=2):
    finger_order = ["index", "middle", "ring"]
    STEP = 0.15

    for cycle in range(cycles):
        print(f"👋 波浪 {cycle + 1}/{cycles}")

        for name in finger_order:
            CloseFinger(name)
            time.sleep(STEP)

        for name in finger_order:
            OpenFinger(name)
            time.sleep(STEP)

        time.sleep(STEP)


def main():
    print("=" * 50)
    print("🦾 AmazingHand — 开机打招呼动画")
    print("=" * 50)

    for sid in range(1, 9):
        c.write_torque_enable(sid, 1)
    time.sleep(0.2)

    try:
        print("\n准备...")
        OpenAll()
        time.sleep(1)

        wave_hello(cycles=2)

        print("\n回到张开...")
        OpenAll()
        time.sleep(0.5)

        print("\n✅ 动画完成！")

    except KeyboardInterrupt:
        print("\n\n⏹ 用户中断")

    finally:
        print("\n🔌 禁用扭矩...")
        for sid in range(1, 9):
            c.write_torque_enable(sid, 2)
        print("✅ 结束")


if __name__ == "__main__":
    main()
