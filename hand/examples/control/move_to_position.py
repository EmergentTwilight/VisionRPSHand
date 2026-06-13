import sys
import os
import time
import argparse
from typing import Any, Tuple
from stservo.sdk import *

# Import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config')))
try:
    from device_config import load_device_port
except ImportError:
    def load_device_port():
        return "/dev/ttyACM0"

# Register Addresses
STS_TORQUE_ENABLE = 40
STS_PRESENT_POSITION_L = 56

# Default settings
DEFAULT_BAUDRATE = 1000000
STS_MOVING_SPEED = 2400
STS_ACC = 50

# Communication results
COMM_SUCCESS = 0

def set_torque(packetHandler: Any, servo_id: int, enable: bool) -> None:
    """
    Enables or disables the servo's torque.
    Raises a RuntimeError if the command fails.
    """
    status_str = "enable" if enable else "disable"
    comm_result, error = packetHandler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE, 1 if enable else 0)
    if comm_result != COMM_SUCCESS or error != 0:
        raise RuntimeError(f"Failed to {status_str} torque for servo ID {servo_id}")
    print(f"Torque {status_str}d for servo ID: {servo_id}")

def check_position(packetHandler: Any, servo_id: int) -> Tuple[int, bool]:
    """
    Reads and returns the current position of the servo.
    """
    position, comm_result, error = packetHandler.read2ByteTxRx(servo_id, STS_PRESENT_POSITION_L)
    if comm_result != COMM_SUCCESS or error != 0:
        return -1, False
    return position, True

def wait_for_move_completion(packetHandler: Any, servo_id: int, timeout: int = 10) -> bool:
    """
    Waits for the servo to stop moving by polling its position.
    The move is considered complete when the position is stable for 0.25 seconds.
    Returns True if the move completes, False on timeout.
    """
    # Initial delay to allow the move to start
    time.sleep(0.5)

    start_time = time.time()
    last_position, success = check_position(packetHandler, servo_id)
    if not success:
        print("Error: Could not read initial position to check for move completion.")
        return False
    
    print(f"Current position: {last_position}")
    time_at_last_change = time.time()

    while time.time() - start_time < timeout:
        current_position, success = check_position(packetHandler, servo_id)
        if not success:
            # On a read error, just continue and try again
            time.sleep(0.05)
            continue

        if current_position != last_position:
            last_position = current_position
            print(f"Current position: {current_position}")
            time_at_last_change = time.time()
        
        # If position has been stable for 0.25 seconds, the move is complete
        if time.time() - time_at_last_change > 0.25:
            print(f"Servo has stopped at position: {current_position}")
            return True

        time.sleep(0.05)  # Poll every 50ms

    print("Warning: Timeout occurred while waiting for the servo to stop.")
    return False

def move_servo(port: str, baudrate: int, servo_id: int, position: int, speed: int, acceleration: int, timeout: int) -> None:
    """
    Connects to a servo and moves it to a specified position.
    """
    portHandler = PortHandler(port)
    packetHandler = sts(portHandler)

    if not portHandler.openPort() or not portHandler.setBaudRate(baudrate):
        print(f"Error: Failed to connect to the servo at {port}")
        return

    print(f"Successfully connected to {port} at {baudrate} baud.")

    try:
        set_torque(packetHandler, servo_id, True)

        # Send the move command
        print(f"Moving servo {servo_id} to position {position}...")
        comm_result, error = packetHandler.WritePosEx(servo_id, position, speed, acceleration)
        if comm_result != COMM_SUCCESS or error != 0:
            print("Error: Failed to write position.")
        else:
            print("Position written successfully.")
            # Wait for the move to finish
            wait_for_move_completion(packetHandler, servo_id, timeout=timeout)

    finally:
        # Always try to disable torque and close the port
        try:
            set_torque(packetHandler, servo_id, False)
        except RuntimeError as e:
            print(e) # If disabling torque fails, print the error but don't crash
        portHandler.closePort()
        print("Port closed.")

def main() -> None:
    """
    Parses command-line arguments and initiates the servo movement.
    """
    parser = argparse.ArgumentParser(description="Move a single ST/SCS servo to a specific position.")
    parser.add_argument(
        "position",
        type=int,
        help="The target position for the servo (0-4095)."
    )
    parser.add_argument(
        "--port",
        type=str,
        default=load_device_port(),
        help="The serial port for the servo controller (e.g., /dev/ttyUSB0 or COM3)."
    )
    parser.add_argument(
        "--servo-id",
        type=int,
        default=1,
        help="The ID of the servo to control."
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=DEFAULT_BAUDRATE,
        help="The baud rate for serial communication."
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=STS_MOVING_SPEED,
        help="The moving speed of the servo."
    )
    parser.add_argument(
        "--acceleration",
        type=int,
        default=STS_ACC,
        help="The acceleration of the servo."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="The timeout in seconds to wait for the move to complete."
    )

    args = parser.parse_args()

    if not (0 <= args.position <= 4095):
        print("Error: Position must be between 0 and 4095.")
        sys.exit(1)


    move_servo(
        port=args.port,
        baudrate=args.baudrate,
        servo_id=args.servo_id,
        position=args.position,
        speed=args.speed,
        acceleration=args.acceleration,
        timeout=args.timeout
    )


if __name__ == "__main__":
    main()
