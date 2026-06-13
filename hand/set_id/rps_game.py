"""
rps_game.py - 石头剪刀布 手势控制
FINGERS 配置与 fist_demo.py 保持一致
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
    c.write_goal_speed(id1, 6)
    c.write_goal_speed(id2, 6)
    pos1 = np.deg2rad(mid1 + off1)
    pos2 = np.deg2rad(mid2 + off2)
    c.write_goal_position(id1, pos1)
    c.write_goal_position(id2, pos2)
    time.sleep(0.01)


def CloseFinger(name):
    cfg = FINGERS[name]
    ids = cfg["ids"]
    mid = cfg["middle"]
    off = cfg["close_offset"]
    MoveFinger(ids[0], ids[1], mid[0], mid[1], off[0], off[1])


def OpenFinger(name):
    cfg = FINGERS[name]
    ids = cfg["ids"]
    mid = cfg["middle"]
    off = cfg["open_offset"]
    MoveFinger(ids[0], ids[1], mid[0], mid[1], off[0], off[1])


def rock():
    print("🪨 石头")
    for name in FINGERS:
        CloseFinger(name)


def scissors():
    print("✂️  剪刀")
    OpenFinger("index")
    OpenFinger("middle")
    CloseFinger("ring")
    CloseFinger("thumb")


def paper():
    print("📄 布")
    for name in FINGERS:
        OpenFinger(name)


def main():
    print("=" * 50)
    print("🦾 AmazingHand — 石头剪刀布")
    print("=" * 50)

    for sid in range(1, 9):
        c.write_torque_enable(sid, 1)

    print("\n输入指令:")
    print("  1 或 石头 → 🪨 石头")
    print("  2 或 剪刀 → ✂️  剪刀")
    print("  3 或 布   → 📄 布")
    print("  q         → 退出\n")

    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd in ("q", "quit", "exit"):
                print("👋 退出")
                break
            elif cmd in ("1", "石头", "rock"):
                rock()
            elif cmd in ("2", "剪刀", "scissors"):
                scissors()
            elif cmd in ("3", "布", "paper"):
                paper()
            else:
                print("❌ 无效输入，请输入 1/2/3 或 石头/剪刀/布")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n⏹ 用户中断")

    finally:
        print("\n🔌 禁用扭矩...")
        for sid in range(1, 9):
            c.write_torque_enable(sid, 2)
        print("✅ 结束")


if __name__ == "__main__":
    main()
