# VisionRPSHand

基于 NVIDIA Jetson Orin Nano 的视觉引导灵巧手猜拳机器人。

## 项目概述

结合计算机视觉、手势识别和灵巧手控制，实现自动猜拳对战。

## 硬件平台

- **主控**: NVIDIA Jetson Orin Nano (CUDA 12.6)
- **灵巧手**: AmazingHand（串口控制，8 DOF）
- **视觉**: 摄像头（待定）

## 开发环境

- Python 3.10
- CUDA 12.6
- Jetson GPIO 库

## 文档

- `docs/AmazingHand/` - 灵巧手硬件项目
- `docs/PINOUT_JETSON_ORIN_NANO.md` - GPIO 引脚参考

## 许可

MIT License
