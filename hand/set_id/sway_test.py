"""
sway_test.py - 单指左右摆动测试
两个舵机独立控制，不再严格相反同步
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
    serial_port="COM13",
    baudrate=1000000,
    timeout=0.5,
)


def move_servo(servo_id, angle_deg):
    try:
        c.write_goal_speed(servo_id, 6)
        pos = np.deg2rad(angle_deg)
        c.write_goal_position(servo_id, pos)
    except RuntimeError as e:
        print(f"  ⚠️  ID {servo_id} 移动超时 ({e})")


def move_both(id1, id2, angle1, angle2):
    try:
        c.write_goal_speed(id1, 6)
        c.write_goal_speed(id2, 6)
        pos1 = np.deg2rad(angle1)
        pos2 = np.deg2rad(angle2)
        c.write_goal_position(id1, pos1)
        c.write_goal_position(id2, pos2)
    except RuntimeError as e:
        print(f"  ⚠️  移动超时 ({e})")


def go_home(ids):
    for name, cfg in FINGERS.items():
        if cfg["ids"] == ids:
            mid = cfg["middle"]
            off = cfg["open_offset"]
            move_both(ids[0], ids[1],
                      mid[0] + off[0], mid[1] + off[1])
            return
    move_both(ids[0], ids[1], 0, 0)


def go_home_all():
    for name, cfg in FINGERS.items():
        ids = cfg["ids"]
        mid = cfg["middle"]
        off = cfg["open_offset"]
        move_both(ids[0], ids[1],
                  mid[0] + off[0], mid[1] + off[1])


def read_pos(servo_id):
    rad = c.read_present_position(servo_id)
    return float(np.rad2deg(rad).item())


def interactive():
    print("=" * 60)
    print("🦾 单指左右摆动测试")
    print("=" * 60)
    print("\n输入两个舵机的目标角度，观察手指 motion。")
    print("  - 同号（如 +30, +30）→ 左右摆动 (abduction)")
    print("  - 异号（如 +30, -30）→ 弯曲/伸直 (flexion)")
    print("  - 一个动一个不动     → 扭转\n")

    fid = input("选择手指 (index/middle/ring/thumb): ").strip().lower()
    if fid not in FINGERS:
        print("❌ 无效手指")
        return

    cfg = FINGERS[fid]
    ids = cfg["ids"]
    mid = cfg["middle"]
    open_off = cfg["open_offset"]
    home1 = mid[0] + open_off[0]
    home2 = mid[1] + open_off[1]

    print(f"  选中的手指: {fid}  (ID {ids[0]}, {ids[1]})")
    print(f"  零位（open）: ID{ids[0]} = {home1:+.1f}°, ID{ids[1]} = {home2:+.1f}°")

    print("\n收起其他手指...")
    for name, cfg2 in FINGERS.items():
        if cfg2["ids"] != ids:
            m = cfg2["middle"]
            o = cfg2["close_offset"]
            move_both(cfg2["ids"][0], cfg2["ids"][1],
                      m[0] + o[0], m[1] + o[1])
    time.sleep(1)

    print(f"选中的手指 ({fid}) 回到 open 零位...")
    go_home(ids)
    time.sleep(1)

    try:
        while True:
            print(f"\n当前: ID{ids[0]} = {read_pos(ids[0]):+.1f}°  ID{ids[1]} = {read_pos(ids[1]):+.1f}°")
            cmd = input("输入 ID1° ID2° (如 30 -30，回车退出): ").strip()

            if not cmd:
                break

            parts = cmd.split()
            if len(parts) != 2:
                print("❌ 格式错误，请输入两个角度值")
                continue

            try:
                a1, a2 = float(parts[0]), float(parts[1])
            except ValueError:
                print("❌ 请输入数字")
                continue

            move_both(ids[0], ids[1], a1, a2)
            time.sleep(1.5)
            print(f"  实际: ID{ids[0]} = {read_pos(ids[0]):+.1f}°  ID{ids[1]} = {read_pos(ids[1]):+.1f}°")

    except KeyboardInterrupt:
        print("\n\n⏹ 中断")

    finally:
        print("\n所有手指回到 open 零位...")
        go_home_all()
        time.sleep(0.5)


def auto_sway():
    print("=" * 60)
    print("🦾 自动摆动演示")
    print("=" * 60)

    ids = [1, 2]
    fid = "index"
    cfg = FINGERS[fid]
    mid = cfg["middle"]
    open_off = cfg["open_offset"]
    home1 = mid[0] + open_off[0]
    home2 = mid[1] + open_off[1]

    for sid in range(1, 9):
        c.write_torque_enable(sid, 1)

    go_home_all()
    time.sleep(1)

    def demo_step(label, a1, a2, t=1.5):
        print(f"  {label}")
        move_both(ids[0], ids[1], a1, a2)
        time.sleep(t)
        move_both(ids[0], ids[1], home1, home2)
        time.sleep(0.8)

    def demo_swing(label, moves, repeat=1):
        print(f"  {label}")
        for _ in range(repeat):
            for a1, a2 in moves:
                move_both(ids[0], ids[1], a1, a2)
                time.sleep(0.35)
        move_both(ids[0], ids[1], home1, home2)
        time.sleep(0.8)

    try:
        print(f"\n演示手指: {fid}  |  open 零位: {home1:+.0f}°, {home2:+.0f}°\n")

        print("1️⃣  弯曲 (flexion) — 两舵机反向:")
        demo_step("  +30, -30", home1 + 30, home2 - 30)
        demo_step("  +60, -60", home1 + 60, home2 - 60)

        print("\n2️⃣  左右摆动 (abduction) — 两舵机同向:")
        demo_step("  向左摆", home1 + 30, home2 + 30)
        demo_step("  向右摆", home1 - 30, home2 - 30)

        print("\n3️⃣  单侧动 — 扭转:")
        demo_step("  ID1+40, ID2不动", home1 + 40, home2)
        demo_step("  ID1-40, ID2不动", home1 - 40, home2)
        demo_step("  ID1不动, ID2+40", home1, home2 + 40)
        demo_step("  ID1不动, ID2-40", home1, home2 - 40)

        print("\n4️⃣  连续摆动 (左右 x3):")
        demo_swing("", [(home1 + 30, home2 + 30),
                        (home1 - 30, home2 - 30)], repeat=3)

        print("\n5️⃣  连续弯曲 (x3):")
        demo_swing("", [(home1 + 60, home2 - 60),
                        (home1, home2)], repeat=3)

        print("\n✅ 演示完成！")

    except KeyboardInterrupt:
        print("\n\n⏹ 中断")

    finally:
        print("\n回到 open 零位...")
        go_home_all()
        time.sleep(0.5)
        for sid in range(1, 9):
            c.write_torque_enable(sid, 2)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        auto_sway()
    else:
        interactive()
