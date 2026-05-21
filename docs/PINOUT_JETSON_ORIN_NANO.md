# Jetson Orin Nano GPIO 引脚参考 (已验证)

## 数据来源
- ✅ NVIDIA 官方 `Jetson.GPIO` 库
- ✅ JetsonHacks 社区参考
- ✅ 实际硬件验证

## PWM 引脚 (3 个)

| 物理引脚 | GPIO 名称 | PWM 芯片 | 用途 | 验证 |
|---------|----------|----------|------|------|
| 15 | GPIO12 | pwmchip0 (3280000.pwm) | 舵机/电机 | ✅ 已验证 |
| 32 | GPIO07 | pwmchip3 (32e0000.pwm) | 舵机/电机 | ✅ 已验证 |
| 33 | GPIO13 | pwmchip2 (32c0000.pwm) | 舵机/电机 | ✅ 已验证 |

## 完整 GPIO 引脚表 (22 个)

| 引脚 | GPIO 名称 | Linux GPIO | 芯片 | 功能 |
|------|----------|-----------|------|------|
| 7 | GPIO09 | 144 | tegra234-gpio | GPIO |
| 11 | UART1_RTS | 112 | tegra234-gpio | UART/GPIO |
| 12 | I2S0_SCLK | 50 | tegra234-gpio | I2S/GPIO |
| 13 | SPI1_SCK | 122 | tegra234-gpio | SPI/GPIO |
| 15 | GPIO12 | 85 | tegra234-gpio | **PWM** |
| 16 | SPI1_CS1 | 126 | tegra234-gpio | SPI/GPIO |
| 18 | SPI1_CS0 | 125 | tegra234-gpio | SPI/GPIO |
| 19 | SPI0_MOSI | 135 | tegra234-gpio | SPI/GPIO |
| 21 | SPI0_MISO | 134 | tegra234-gpio | SPI/GPIO |
| 22 | SPI1_MISO | 123 | tegra234-gpio | SPI/GPIO |
| 23 | SPI0_SCK | 133 | tegra234-gpio | SPI/GPIO |
| 24 | SPI0_CS0 | 136 | tegra234-gpio | SPI/GPIO |
| 26 | SPI0_CS1 | 137 | tegra234-gpio | SPI/GPIO |
| 29 | GPIO01 | 105 | tegra234-gpio | GPIO |
| 31 | GPIO11 | 106 | tegra234-gpio | GPIO |
| 32 | GPIO07 | 41 | tegra234-gpio | **PWM** |
| 33 | GPIO13 | 43 | tegra234-gpio | **PWM** |
| 35 | I2S0_FS | 53 | tegra234-gpio | I2S/GPIO |
| 36 | UART1_CTS | 113 | tegra234-gpio | UART/GPIO |
| 37 | SPI1_MOSI | 124 | tegra234-gpio | SPI/GPIO |
| 38 | I2S0_SDIN | 52 | tegra234-gpio | I2S/GPIO |
| 40 | I2S0_SDOUT | 51 | tegra234-gpio | I2S/GPIO |

## 使用方法

```python
import Jetson.GPIO as GPIO

# 使用物理引脚编号 (推荐)
GPIO.setmode(GPIO.BOARD)

# 设置 PWM
pwm = GPIO.PWM(15, 50)  # 引脚 15, 50Hz
pwm.start(7.5)  # 7.5% duty cycle (中位)

# 清理
GPIO.cleanup()
```

## 重要警告
- GPIO 输出电压: **3.3V**
- 最大输出电流: **~4mA per pin**
- 舵机/电机需要外部电源 (5V+)
- 使用驱动板保护 Jetson GPIO

## 参考链接
- https://github.com/NVIDIA/jetson-gpio
- https://jetsonhacks.com/nvidia-jetson-orin-nano-gpio-header-pinout/
