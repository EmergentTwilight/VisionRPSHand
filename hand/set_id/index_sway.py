"""
index_sway.py - 三指收起，食指连续流畅摆动
"""

import time
import math
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
    serial_port="COM13",
    baudrate=1000000,
    timeout=0.5,
)


def move_both(id1, id2, angle1, angle2):
    try:
        c.write_goal_speed(id1, 7)
        c.write_goal_speed(id2, 7)
        c.write_goal_position(id1, np.deg2rad(angle1))
        c.write_goal_position(id2, np.deg2rad(angle2))
    except RuntimeError:
        pass


def close_finger(name):
    cfg = FINGERS[name]
    mid = cfg["middle"]
    off = cfg["close_offset"]
    move_both(cfg["ids"][0], cfg["ids"][1],
              mid[0] + off[0], mid[1] + off[1])


def open_all():
    for name, cfg in FINGERS.items():
        mid = cfg["middle"]
        off = cfg["open_offset"]
        move_both(cfg["ids"][0], cfg["ids"][1],
                  mid[0] + off[0], mid[1] + off[1])


LEFT_1, LEFT_2   = 60, -150
RIGHT_1, RIGHT_2 = 150, -60

CENTER_1 = (LEFT_1 + RIGHT_1) / 2
AMP_1    = (RIGHT_1 - LEFT_1) / 2
CENTER_2 = (LEFT_2 + RIGHT_2) / 2
AMP_2    = (RIGHT_2 - LEFT_2) / 2


def swing_index(freq_hz=0.8, duration_s=None):
    t0 = time.time()
    update_interval = 0.03

    while True:
        t = time.time() - t0
        if duration_s and t >= duration_s:
            break

        phase = 2 * math.pi * freq_hz * t
        a1 = CENTER_1 + AMP_1 * math.sin(phase)
        a2 = CENTER_2 + AMP_2 * math.sin(phase)

        move_both(1, 2, a1, a2)
        time.sleep(update_interval)


def main():
    print("=" * 50)
    print("🦾 食指连续流畅摆动")
    print("  中指/无名指/拇指 — 收起")
    print("=" * 50)

    for sid in range(1, 9):
        c.write_torque_enable(sid, 1)
    time.sleep(0.2)

    try:
        print("\n收起其他手指...")
        for name in ["middle", "ring", "thumb"]:
            close_finger(name)
        time.sleep(1)

        print("食指回到中位...")
        move_both(1, 2, CENTER_1, CENTER_2)
        time.sleep(0.5)

        print(f"\n连续摆动 (频率 {0.8}Hz, Ctrl+C 停止)\n")
        swing_index(freq_hz=0.8)

    except KeyboardInterrupt:
        print("\n\n⏹ 用户中断")

    finally:
        print("\n所有手指回到 open 零位...")
        open_all()
        time.sleep(0.5)
        for sid in range(1, 9):
            c.write_torque_enable(sid, 2)
        print("✅ 结束")


if __name__ == "__main__":
    main()
