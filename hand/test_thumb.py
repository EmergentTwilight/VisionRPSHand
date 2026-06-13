"""测试AmazingHand拇指手势"""
import sys
sys.path.insert(0, '../set_id')
import time
import numpy as np
from rustypot import Scs0009PyController

FINGERS = {
    "index": {"ids": [1, 2], "middle": [0.0, 0.0], "close_offset": [-30, 30], "open_offset": [90, -90]},
    "middle": {"ids": [3, 4], "middle": [0.0, 0.0], "close_offset": [-120, 120], "open_offset": [30, -30]},
    "ring": {"ids": [5, 6], "middle": [0.0, 0.0], "close_offset": [-110, 110], "open_offset": [20, -20]},
    "thumb": {"ids": [7, 8], "middle": [0.0, 0.0], "close_offset": [-110, 110], "open_offset": [20, -20]},
}

c = Scs0009PyController(serial_port="/dev/ttyACM0", baudrate=1000000, timeout=0.5)

def MoveFinger(id1, id2, mid1, mid2, off1, off2):
    c.write_goal_speed(id1, 6)
    c.write_goal_speed(id2, 6)
    c.write_goal_position(id1, np.deg2rad(mid1 + off1))
    c.write_goal_position(id2, np.deg2rad(mid2 + off2))

# 使能舵机
for sid in range(1, 9): c.write_torque_enable(sid, 1)
time.sleep(0.2)

print("👍 拇指手势...")

# 拇指张开，其他闭合
cfg = FINGERS["thumb"]
MoveFinger(cfg["ids"][0], cfg["ids"][1], cfg["middle"][0], cfg["middle"][1], 
           cfg["open_offset"][0], cfg["open_offset"][1])

for name in ["index", "middle", "ring"]:
    cfg = FINGERS[name]
    MoveFinger(cfg["ids"][0], cfg["ids"][1], cfg["middle"][0], cfg["middle"][1],
               cfg["close_offset"][0], cfg["close_offset"][1])

time.sleep(3)
print("🔌 结束")
for sid in range(1, 9): c.write_torque_enable(sid, 2)
