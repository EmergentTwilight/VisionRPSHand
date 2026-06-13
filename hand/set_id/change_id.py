"""
change_id.py - 修改 SC09 舵机 ID（对照 Arduino SCSCL 库实现）
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from stservo.sdk import *

PORT = "COM9"
BAUDRATE = 1000000


def main():
    old_id = None
    new_id = None

    for i, arg in enumerate(sys.argv):
        if arg == "--old" and i + 1 < len(sys.argv):
            old_id = int(sys.argv[i + 1])
        elif arg == "--new" and i + 1 < len(sys.argv):
            new_id = int(sys.argv[i + 1])

    portHandler = PortHandler(PORT)
    if not portHandler.openPort():
        print(f"❌ 无法打开串口 {PORT}")
        return
    if not portHandler.setBaudRate(BAUDRATE):
        print("❌ 无法设置波特率")
        portHandler.closePort()
        return
    print(f"✅ 串口 {PORT} 已打开\n")

    ph = scscl(portHandler)

    # 扫描当前所有舵机
    print("=== 扫描舵机 ===")
    found = []
    for sid in range(254):
        model, result, error = ph.ping(sid)
        if result == COMM_SUCCESS:
            found.append((sid, model))
            print(f"  ✓ ID {sid:3d}  Model={model}")

    if not found:
        print("\n⚠️  没有找到任何舵机")
        portHandler.closePort()
        return

    print(f"\n当前舵机: {[s[0] for s in found]}")

    if old_id is None:
        try:
            old_id = int(input("请输入要修改的舵机当前 ID: ").strip())
        except:
            print("输入无效")
            portHandler.closePort()
            return

    if new_id is None:
        try:
            new_id = int(input("请输入新的舵机 ID (0~253): ").strip())
        except:
            print("输入无效")
            portHandler.closePort()
            return

    if new_id < 0 or new_id > 253:
        print("❌ ID 范围 0~253")
        portHandler.closePort()
        return

    # 确认旧 ID 存在
    model, result, error = ph.ping(old_id)
    if result != COMM_SUCCESS:
        print(f"❌ 舵机 ID={old_id} 无响应")
        portHandler.closePort()
        return

    print(f"\n{'='*40}")
    print(f"修改 ID: {old_id} → {new_id}")
    print(f"{'='*40}")

    # ----- 对照 Arduino 代码：-----
    # sc.unLockEprom(ID_ChangeFrom);
    # sc.writeByte(ID_ChangeFrom, SCSCL_ID, ID_Changeto);
    # sc.LockEprom(ID_Changeto);

    # 1. 解锁 EPROM（对旧 ID 操作，写 0 到地址 48）
    print("1️⃣ 解锁 EPROM (addr 48 ← 0)")
    ph.unLockEprom(old_id)
    time.sleep(0.05)

    # 2. 写入新 ID（对旧 ID 的地址 5 写入新值）
    print(f"2️⃣ 写入新 ID (addr 5 ← {new_id})")
    result, error = ph.write1ByteTxRx(old_id, 5, new_id)
    if result != COMM_SUCCESS or error != 0:
        print(f"   写入失败: comm={result}, error={error}")
        portHandler.closePort()
        return
    time.sleep(0.1)

    # 3. 验证新 ID
    print("3️⃣ 验证新 ID...")
    model, result, error = ph.ping(new_id)
    if result == COMM_SUCCESS:
        print(f"   ✅ 新 ID {new_id} 响应正常")
    else:
        print(f"   ⚠️ 新 ID 无响应，重新扫描...")
        for sid in range(254):
            m, r, e = ph.ping(sid)
            if r == COMM_SUCCESS:
                print(f"   发现舵机 ID={sid}")

    # 4. 锁定 EPROM（对新 ID 操作，写 1 到地址 48）
    print("4️⃣ 锁定 EPROM (addr 48 ← 1)")
    ph.LockEprom(new_id)

    print(f"\n✅ 修改成功！{old_id} → {new_id}")
    print("   掉电后可保存，重启验证即可")

    portHandler.closePort()
    print("🔌 串口已关闭")


if __name__ == "__main__":
    main()
