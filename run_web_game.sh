#!/bin/bash
# 启动Web版RPS游戏

cd /home/nvidia/VisionRPSHand/web_rps_game

# 激活venv
source /home/nvidia/VisionRPSHand/venv/bin/activate

# 安装依赖（如果需要）
pip install -q flask flask-socketio 2>/dev/null

echo "启动Web服务器..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止"

python3 app.py
