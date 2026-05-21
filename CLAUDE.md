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

## GPIO Reference

See `docs/PINOUT_JETSON_ORIN_NANO.md` for complete pinout.

**Key PWM Pins**:
- Pin 15 → pwmchip0 (3280000.pwm)
- Pin 32 → pwmchip3 (32e0000.pwm)
- Pin 33 → pwmchip2 (32c0000.pwm)

## AmazingHand Control

The hand uses serial communication, not direct GPIO PWM.

Example from `docs/AmazingHand/PythonExample/AmazingHand_Demo.py`:
```python
from rustypot import Scs0009PyController

c = Scs0009PyController(
    serial_port="COM11",
    baudrate=1000000,
    timeout=0.5,
)
```

On Jetson, the serial port would be `/dev/ttyTHS0` or similar.

## Environment

**CUDA** (already configured):
```bash
export CUDA_HOME=/usr/local/cuda-12.6
export PATH=$CUDA_HOME/bin:$PATH
```

**GPIO**: Use `Jetson.GPIO` library
