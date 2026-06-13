# VisionRPSHand - Project Documentation for Claude

## Project

VisionRPSHand - 基于视觉和灵巧手的猜拳机器人

## Hardware Platform

**Main Controller**: NVIDIA Jetson Orin Nano Developer Kit (Super)
- SoC: Orin (nvgpu), ARM64 architecture
- RAM: 8GB
- CUDA: 12.6
- GPIO: 22 pins, 3 PWM channels

**Dexterous Hand**: AmazingHand
- 8 DOF humanoid hand with 4 fingers
- 2 phalanxes per finger
- Feetech SCS0009 servos (serial bus control)
- Controlled via `rustypot` library

## Directory Structure

```
VisionRPSHand/
├── app/                # 主游戏应用
│   ├── main.py        # 游戏入口
│   ├── templates/     # Web界面
│   └── high_scores.json
├── hand/               # 灵巧手控制
├── gesture/            # 手势识别
│   ├── data/           # 训练数据
│   └── gesture_train.csv
├── docs/               # 文档
├── venv/               # 虚拟环境
└── run.sh              # 启动脚本
```

## Environment

### Python Virtual Environment

**Location**: `/home/nvidia/VisionRPSHand/venv`

**Activation**:
```bash
source /home/nvidia/VisionRPSHand/venv/bin/activate
```

**Installed Packages**:
- mediapipe==0.10.18
- opencv-python==4.11.0
- numpy
- flask
- flask-socketio
- rustypot

### Hardware

- **灵巧手**: `/dev/ttyACM0` (USB串口)
- **摄像头**: `/dev/video0`

## Gesture Recognition

**Location**: `/home/nvidia/VisionRPSHand/gesture/`

**Training Data**: `gesture/data/gesture_train.csv`

**Supported Gestures**:
- 0: rock (石头)
- 5: paper (布)
- 9: scissors (剪刀)
- 10: ok (OK)

### Adding New Gestures

```bash
cd gesture
python gather_dataset.py
python gather_thumb.py
```

## Dexterous Hand Control

**Location**: `/home/nvidia/VisionRPSHand/hand/`

**Test Scripts**:
- `test_rock.py` - 测试石头手势
- `test_rps.py` - 测试猜拳手势
- `test_gestures.py` - 测试所有手势

## Game Application

**Entry**: `/home/nvidia/VisionRPSHand/app/main.py`

**Run**:
```bash
./run.sh
```

**Access**: `http://localhost:5000`

## Game Flow

1. **monitoring**: 检测OK手势开始游戏
2. **countdown**: 3-2-1倒计时
   - T-0.2: 机器开始出拳
   - T=0: 显示0
   - T+0.2: 识别用户手势
3. **result**: 显示结果
4. **paused**: 准备下一局
5. **game_over**: 游戏结束（检测到OK或连续3次无效）
