# 🤖 STServo Python Library

> **Note:** This library is actively improved and modified based on the [official Waveshare STServo control library](https://files.waveshare.com/wiki/Bus_Servo_Driver_HAT_A/STServo_Python.zip). Enhancements, bug fixes, and new features are added for better usability and reliability.
Control your Waveshare STServos easily with Python! This library provides both a simple GUI application and a powerful programming interface for STServo control.

## ✨ What You Can Do

- **🖱️ GUI Control**: Point-and-click interface - no coding required!
- **🔍 Auto-Discovery**: Automatically find and connect to your servos
- **🎯 Precise Control**: Move servos to exact positions or run them continuously
- **📊 Real-time Monitoring**: See servo status, load, and position live
- **🔧 Easy Setup**: Simple installation and configuration
- **👥 Multi-Servo**: Control multiple servos at once

## 🚀 Quick Start (2 mins)

### Step 1: Install the Package
```bash
# Navigate to the project folder
cd waveshare_stservo_python

# Install the package
pip install -e .
```

### Step 2: Connect Your Servo
1. Connect your STServo to your computer via USB-to-TTL adapter
2. Note the serial port (usually `/dev/ttyACM0` on Linux, `COM3` on Windows)

### Step 3: Launch the GUI
```bash
stservo-gui
```

That's it! The GUI will open and you can start controlling your servos immediately.

## 🖥️ Using the GUI Application

The GUI is the easiest way to get started:

1. **Launch**: Run `stservo-gui` in your terminal
2. **Connect**: The app auto-detects your serial port
3. **Discover**: Click "Scan for Servos" to find connected servos
4. **Control**: Use sliders and buttons to move your servos
5. **Monitor**: Watch real-time position, load, and temperature data

### GUI Features
- 🔍 **Automatic Servo Detection** - finds all connected servos
- 🎛️ **Position Control** - precise angle positioning
- 🏃 **Speed Control** - set movement speed  
- 🔄 **Wheel Mode** - continuous rotation
- 📈 **Live Monitoring** - real-time servo data
- ⚙️ **Settings** - change servo IDs, limits, and calibration

<img width="1020" height="755" alt="Screenshot from 2025-08-06 18-55-57" src="https://github.com/user-attachments/assets/b3f5b3d9-ae0a-4d5b-a184-6a13a79c087c" />

## 🎯 Try the Examples

We've included lots of examples to help you learn:

```bash
# Move servo with ID 1 to position 500 at speed 2000, timeout 20s
python -m examples.control.move_to_position --port COM3 --servo-id 1 --speed 2000 --timeout 20 500

# Test connection to your servo
python -m examples.discovery.ping_all

# Toggle servo torque  
python -m examples.advanced.torque
```

## ⚙️ Configuration

### Set Your Serial Port
Edit `config/device_port.yaml` to match your setup:
```yaml
device_port: "/dev/ttyACM0"  # Linux/Mac
# device_port: "COM3"        # Windows
```

---

### 📄 License
MIT License - use it freely in your projects!

### 🤝 Contributing
Pull requests welcome! Help make this library even better!
