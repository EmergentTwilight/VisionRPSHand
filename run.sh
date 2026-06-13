#!/bin/bash
# 启动VisionRPSHand猜拳游戏

echo "🎮 启动VisionRPSHand猜拳游戏..."

# 设置串口权限
echo 'nvidia' | sudo -S chmod 666 /dev/ttyACM0 2>/dev/null

# 激活虚拟环境
source /home/nvidia/VisionRPSHand/venv/bin/activate

# 启动游戏
python app/main.py
