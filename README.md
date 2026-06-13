# VisionRPSHand - 基于视觉和灵巧手的猜拳机器人

## 项目简介

使用MediaPipe进行手势识别，通过Web界面实时控制灵巧手进行猜拳游戏。

## 硬件平台

- **主控制器**: NVIDIA Jetson Orin Nano
- **灵巧手**: AmazingHand (8 DOF)
- **摄像头**: USB摄像头

## 目录结构

```
VisionRPSHand/
├── app/                # 主游戏应用
│   ├── main.py        # 游戏入口
│   └── templates/     # Web界面
├── hand/               # 灵巧手控制
├── gesture/            # 手势识别
├── docs/               # 文档
├── venv/               # 虚拟环境
└── run.sh              # 启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 运行游戏

```bash
./run.sh
```

### 3. 访问游戏

浏览器打开: `http://localhost:5000`

## 游戏玩法

1. **👌 OK** 手势开始游戏
2. 倒计时后做出 **✊✋✌️** 手势
3. **👌 OK** 手势结束游戏

## 手势识别

支持手势:
- ✊ 石头 (Rock)
- ✋ 布 (Paper)
- ✌️ 剪刀 (Scissors)
- 👌 OK (开始/结束游戏)

## 开发

### 添加新手势

```bash
cd gesture
python gather_dataset.py
python gather_thumb.py
```

### 测试灵巧手

```bash
cd hand
python test_rock.py
python test_rps.py
```

## 硬件连接

- 灵巧手: `/dev/ttyACM0`
- 摄像头: `/dev/video0`

## 许可证

MIT License
