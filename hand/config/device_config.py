#!/usr/bin/env python
"""
Device Configuration Utilities
Helper functions for loading device configuration from YAML files
"""

import os
import yaml

def load_device_port():
    """
    Load device port from YAML configuration file
    
    Returns:
        str: Device port path, defaults to '/dev/ttyACM0' if not found
    """
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'device_port.yaml')
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            port = config.get('device_port', '/dev/ttyACM0')
            print(f"Using device port from config: {port}")
            return port
    except FileNotFoundError:
        print("Warning: device_port.yaml not found. Using default port /dev/ttyACM0")
        print("Run check_port.py first to detect your device port.")
        return '/dev/ttyACM0'
    except Exception as e:
        print(f"Warning: Error reading device_port.yaml: {e}")
        return '/dev/ttyACM0'

def load_servo_config():
    """
    Load servo configuration from YAML file (for future use)
    
    Returns:
        dict: Configuration dictionary with servo settings
    """
    try:
        config_file = os.path.join(os.path.dirname(__file__), '..', 'servo_config.yaml')
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            return config
    except FileNotFoundError:
        # Return default configuration
        return {
            'baudrate': 1000000,
            'default_servo_id': 1,
            'timeout': 1000
        }
    except Exception as e:
        print(f"Warning: Error reading servo_config.yaml: {e}")
        return {
            'baudrate': 1000000,
            'default_servo_id': 1,
            'timeout': 1000
        }

def save_servo_config(servo_id, model_number=None):
    """
    Save discovered servo configuration to YAML file
    
    Args:
        servo_id (int): The discovered servo ID
        model_number (int, optional): The servo model number
    """
    try:
        config_file = os.path.join(os.path.dirname(__file__), '..', 'servo_config.yaml')
        config = {
            'discovered_servo_id': servo_id,
            'baudrate': 1000000,
            'last_updated': __import__('datetime').datetime.now().isoformat()
        }
        if model_number is not None:
            config['model_number'] = model_number
            
        with open(config_file, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        print(f"Servo configuration saved: ID={servo_id}")
    except Exception as e:
        print(f"Warning: Could not save servo configuration: {e}")
