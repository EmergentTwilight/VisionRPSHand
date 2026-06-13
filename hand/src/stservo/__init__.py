"""
STServo Python Library

A comprehensive Python library for controlling Waveshare STServos.

This package provides:
- Complete SDK for STServo communication
- GUI application for servo control
- Utilities for discovery and configuration
- Example scripts for all functionality
"""

__version__ = "1.0.0"
__author__ = "iltlo"
__email__ = "iltlo@connect.hku.hk"

# Import main SDK components
from .utils import check_port


try:
    from .sdk import (
        PortHandler,
        sts,
        COMM_SUCCESS,
        STS_TORQUE_ENABLE,
        STS_ID,
        STS_PRESENT_POSITION_L,
        STS_PRESENT_SPEED_L,
        STS_PRESENT_LOAD_L,
        STS_MODE,
    )
    
    # Import utilities (optional)
    try:
        from .utils import find_servo
        __all__ = [
            "PortHandler",
            "sts", 
            "COMM_SUCCESS",
            "STS_TORQUE_ENABLE",
            "STS_ID",
            "STS_PRESENT_POSITION_L",
            "STS_PRESENT_SPEED_L",
            "STS_PRESENT_LOAD_L",
            "STS_MODE",
            "find_servo",
            "check_port",
        ]
    except ImportError:
        __all__ = [
            "PortHandler",
            "sts", 
            "COMM_SUCCESS",
            "STS_TORQUE_ENABLE", 
            "STS_ID",
            "STS_PRESENT_POSITION_L",
            "STS_PRESENT_SPEED_L",
            "STS_PRESENT_LOAD_L", 
            "STS_MODE",
        ]
        
except ImportError as e:
    print(f"Warning: Could not import SDK components: {e}")
    __all__ = []
