#!/usr/bin/env python
"""
STServo Control GUI
A comprehensive GUI application for controlling STServos with features like:
- Servo discovery (ping)
- ID management 
- Position control
- Real-time monitoring
- Torque control
- Calibration
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
import os
from datetime import datetime

# Import from the reorganized package structure
from ..sdk import *

# Import config functions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config')))
try:
    from device_config import load_device_port, save_servo_config
except ImportError:
    # Fallback if config import fails
    def load_device_port():
        return "/dev/ttyACM0"
    def save_servo_config(*args, **kwargs):
        pass

class STServoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("STServo Control Panel")
        self.root.geometry("1000x700")
        
        # Initialize variables
        self.port_handler = None
        self.packet_handler = None
        self.connected = False
        self.monitoring = False
        self.current_servo_id = 0           # Changed to 0 (valid range start)
        self.device_name = load_device_port()
        self.baudrate = 1000000
        
        # Default parameters
        self.default_params = {
            'position': 2048,
            'speed': 1500,
            'acceleration': 50,
            'wheel_speed': 0,
            'servo_id': 0,          # Changed to 0 (valid range start)
            'min_pos': 0,
            'max_pos': 4095,
            'scan_start': 0,
            'scan_end': 253         # Changed to 253 (full range scan)
        }
        
        # Sync operation variables
        self.sync_servo_list = []
        self.control_mode = "single"  # "single" or "sync" mode
        self.is_scanning = False  # Track scanning state
        
        # Create the GUI
        self.create_widgets()
        
        # Try to connect on startup
        self.connect_servo()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection Tab
        self.create_connection_tab(notebook)
        
        # Discovery Tab
        self.create_discovery_tab(notebook)
        
        # Control Tab
        self.create_control_tab(notebook)
        
        # Monitor Tab
        self.create_monitor_tab(notebook)
        
        # Settings Tab
        self.create_settings_tab(notebook)
        
        # Status bar
        self.create_status_bar()
    
    def create_connection_tab(self, notebook):
        """Create connection and basic info tab"""
        conn_frame = ttk.Frame(notebook)
        notebook.add(conn_frame, text="Connection")
        
        # Connection info
        info_frame = ttk.LabelFrame(conn_frame, text="Connection Info")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Device Port:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.port_label = ttk.Label(info_frame, text=self.device_name)
        self.port_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Baudrate:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.baudrate_label = ttk.Label(info_frame, text=str(self.baudrate))
        self.baudrate_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.status_label = ttk.Label(info_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Connection buttons
        btn_frame = ttk.Frame(info_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.connect_btn = ttk.Button(btn_frame, text="Connect", command=self.connect_servo)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(btn_frame, text="Disconnect", command=self.disconnect_servo, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Current servo
        servo_frame = ttk.LabelFrame(conn_frame, text="Current Servo")
        servo_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(servo_frame, text="Servo ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.servo_id_var = tk.StringVar(value=str(self.default_params['servo_id']))
        self.servo_id_entry = ttk.Entry(servo_frame, textvariable=self.servo_id_var, width=10)
        self.servo_id_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Button(servo_frame, text="Set Active", command=self.set_active_servo).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(servo_frame, text="Ping", command=self.ping_servo).grid(row=0, column=3, padx=5, pady=2)
        
        # Control Mode Selection
        mode_frame = ttk.LabelFrame(conn_frame, text="Control Mode")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="Single Servo Control", variable=self.mode_var, 
                       value="single", command=self.on_mode_change).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="Sync Control Mode", variable=self.mode_var, 
                       value="sync", command=self.on_mode_change).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.mode_status_label = ttk.Label(mode_frame, text="Mode: Single Servo Control", foreground="blue")
        self.mode_status_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Servo List Management (for Sync Mode)
        servo_mgmt_frame = ttk.LabelFrame(conn_frame, text="Servo List Management")
        servo_mgmt_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(servo_mgmt_frame, text="Add Servo ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.add_servo_var = tk.StringVar(value="0")
        ttk.Entry(servo_mgmt_frame, textvariable=self.add_servo_var, width=8).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Button(servo_mgmt_frame, text="Add to List", command=self.add_servo_to_sync).grid(row=0, column=2, padx=5, pady=2)
        ttk.Button(servo_mgmt_frame, text="Clear List", command=self.clear_servo_sync_list).grid(row=0, column=3, padx=5, pady=2)
        
        self.sync_auto_add_button = ttk.Button(servo_mgmt_frame, text="Auto-Add Found", command=self.auto_add_found_servos)
        self.sync_auto_add_button.grid(row=0, column=4, padx=5, pady=2)
        
        # Current servo list display
        list_frame = ttk.Frame(servo_mgmt_frame)
        list_frame.grid(row=1, column=0, columnspan=5, pady=10, sticky=tk.EW)
        
        ttk.Label(list_frame, text="Current Servo List:").pack(side=tk.LEFT, padx=5)
        self.sync_servo_label = ttk.Label(list_frame, text="[]", foreground="blue")
        self.sync_servo_label.pack(side=tk.LEFT, padx=5)
        
        # Auto-Add Progress Display
        progress_frame = ttk.Frame(servo_mgmt_frame)
        progress_frame.grid(row=2, column=0, columnspan=5, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(progress_frame, text="Scan Progress:").pack(side=tk.LEFT, padx=5)
        self.sync_scan_progress = ttk.Progressbar(progress_frame, mode='determinate', length=200)
        self.sync_scan_progress.pack(side=tk.LEFT, padx=5)
        
        self.sync_scan_percentage_label = ttk.Label(progress_frame, text="0%", foreground="green", width=8)
        self.sync_scan_percentage_label.pack(side=tk.LEFT, padx=5)
    
    def create_discovery_tab(self, notebook):
        """Create servo discovery tab"""
        disc_frame = ttk.Frame(notebook)
        notebook.add(disc_frame, text="Discovery")
        
        # Scan controls
        scan_frame = ttk.LabelFrame(disc_frame, text="Servo Discovery")
        scan_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(scan_frame, text="Scan Range:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.scan_start_var = tk.StringVar(value=str(self.default_params['scan_start']))
        ttk.Entry(scan_frame, textvariable=self.scan_start_var, width=5).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(scan_frame, text="to").grid(row=0, column=2, padx=5, pady=2)
        
        self.scan_end_var = tk.StringVar(value=str(self.default_params['scan_end']))
        ttk.Entry(scan_frame, textvariable=self.scan_end_var, width=5).grid(row=0, column=3, padx=5, pady=2)
        
        self.quick_scan_btn = ttk.Button(scan_frame, text="Quick Scan (0-20)", command=self.quick_scan)
        self.quick_scan_btn.grid(row=0, column=4, padx=5, pady=2)
        
        self.full_scan_btn = ttk.Button(scan_frame, text="Full Scan (0-253)", command=self.full_scan)
        self.full_scan_btn.grid(row=0, column=5, padx=5, pady=2)
        
        self.custom_scan_btn = ttk.Button(scan_frame, text="Custom Scan", command=self.custom_scan)
        self.custom_scan_btn.grid(row=1, column=0, padx=5, pady=2)
        
        ttk.Button(scan_frame, text="Reset Scan Defaults", command=self.reset_scan_defaults).grid(row=1, column=5, padx=5, pady=2)
        
        self.scan_progress = ttk.Progressbar(scan_frame, mode='determinate')
        self.scan_progress.grid(row=1, column=1, columnspan=4, sticky=tk.EW, padx=5, pady=2)
        
        # Results
        results_frame = ttk.LabelFrame(disc_frame, text="Found Servos")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for servo list
        columns = ('ID', 'Model', 'Status')
        self.servo_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.servo_tree.heading(col, text=col)
            self.servo_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.servo_tree.yview)
        self.servo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.servo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to select servo
        self.servo_tree.bind('<Double-1>', self.on_servo_select)
    
    def create_control_tab(self, notebook):
        """Create servo control tab"""
        ctrl_frame = ttk.Frame(notebook)
        notebook.add(ctrl_frame, text="Control")
        
        # Mode indicator
        mode_indicator_frame = ttk.LabelFrame(ctrl_frame, text="Current Mode")
        mode_indicator_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.ctrl_mode_label = ttk.Label(mode_indicator_frame, text="Mode: Single Servo Control", foreground="blue")
        self.ctrl_mode_label.pack(padx=5, pady=2)
        
        # Position control
        pos_frame = ttk.LabelFrame(ctrl_frame, text="Position Control")
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pos_frame, text="Target Position:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.target_pos_var = tk.StringVar(value=str(self.default_params['position']))
        self.target_pos_scale = tk.Scale(pos_frame, from_=0, to=4095, orient=tk.HORIZONTAL, 
                                       variable=self.target_pos_var, length=300)
        self.target_pos_scale.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Entry(pos_frame, textvariable=self.target_pos_var, width=8).grid(row=0, column=2, padx=5, pady=2)
        
        ttk.Label(pos_frame, text="Speed:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.speed_var = tk.StringVar(value=str(self.default_params['speed']))
        self.speed_scale = tk.Scale(pos_frame, from_=0, to=4095, orient=tk.HORIZONTAL, 
                variable=self.speed_var, length=300)
        self.speed_scale.grid(row=1, column=1, padx=5, pady=2)
        ttk.Entry(pos_frame, textvariable=self.speed_var, width=8).grid(row=1, column=2, padx=5, pady=2)
        
        ttk.Label(pos_frame, text="Acceleration:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.acc_var = tk.StringVar(value=str(self.default_params['acceleration']))
        self.acc_scale = tk.Scale(pos_frame, from_=0, to=255, orient=tk.HORIZONTAL, 
                variable=self.acc_var, length=300)
        self.acc_scale.grid(row=2, column=1, padx=5, pady=2)
        ttk.Entry(pos_frame, textvariable=self.acc_var, width=8).grid(row=2, column=2, padx=5, pady=2)
        
        control_btn_frame = ttk.Frame(pos_frame)
        control_btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(control_btn_frame, text="Move to Position", command=self.move_to_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_btn_frame, text="Stop", command=self.stop_servo).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_btn_frame, text="Reset to Default", command=self.reset_control_defaults).pack(side=tk.LEFT, padx=5)
        
        # Sync-specific buttons (visible when in sync mode)
        sync_btn_frame = ttk.Frame(pos_frame)
        sync_btn_frame.grid(row=4, column=0, columnspan=3, pady=5)
        
        ttk.Button(sync_btn_frame, text="Sync Write Position", command=self.sync_write_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(sync_btn_frame, text="Sync Stop All", command=self.sync_stop_all).pack(side=tk.LEFT, padx=5)
        
        # Torque control
        torque_frame = ttk.LabelFrame(ctrl_frame, text="Torque Control")
        torque_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(torque_frame, text="Enable Torque", command=self.enable_torque).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(torque_frame, text="Disable Torque", command=self.disable_torque).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(torque_frame, text="Calibrate Center", command=self.calibrate_center).grid(row=0, column=2, padx=5, pady=5)
        
        # Mode Control
        mode_frame = ttk.LabelFrame(ctrl_frame, text="Servo Mode Control")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mode selection buttons
        mode_btn_frame = ttk.Frame(mode_frame)
        mode_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(mode_btn_frame, text="Enable Position Mode", command=self.enable_position_mode).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(mode_btn_frame, text="Enable Wheel Mode", command=self.enable_wheel_mode).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Wheel speed controls
        wheel_speed_frame = ttk.Frame(mode_frame)
        wheel_speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(wheel_speed_frame, text="Wheel Speed:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.wheel_speed_var = tk.StringVar(value=str(self.default_params['wheel_speed']))
        self.wheel_speed_scale = tk.Scale(wheel_speed_frame, from_=-2400, to=2400, orient=tk.HORIZONTAL, 
                                        variable=self.wheel_speed_var, length=300)
        self.wheel_speed_scale.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Button(wheel_speed_frame, text="Set Speed", command=self.set_wheel_speed).grid(row=0, column=2, padx=5, pady=5)
        
        # Sync Read Operations (for Sync Mode)
        sync_read_frame = ttk.LabelFrame(ctrl_frame, text="Sync Read Operations")
        sync_read_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Read controls
        read_ctrl_frame = ttk.Frame(sync_read_frame)
        read_ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(read_ctrl_frame, text="Sync Read Position/Speed", command=self.sync_read_pos_speed).pack(side=tk.LEFT, padx=5)
        ttk.Button(read_ctrl_frame, text="Sync Read All Data", command=self.sync_read_all_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(read_ctrl_frame, text="Clear Results", command=self.clear_sync_results).pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_text_frame = ttk.Frame(sync_read_frame)
        results_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.sync_results_text = scrolledtext.ScrolledText(results_text_frame, height=10, state=tk.DISABLED)
        self.sync_results_text.pack(fill=tk.BOTH, expand=True)
    
    
    def create_monitor_tab(self, notebook):
        """Create monitoring tab"""
        mon_frame = ttk.Frame(notebook)
        notebook.add(mon_frame, text="Monitor")
        
        # Current readings
        readings_frame = ttk.LabelFrame(mon_frame, text="Current Readings")
        readings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Single servo readings (always visible)
        single_frame = ttk.LabelFrame(readings_frame, text="Single Servo Mode")
        single_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # Create labels for single servo readings
        self.pos_reading = ttk.Label(single_frame, text="Position: --")
        self.pos_reading.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.speed_reading = ttk.Label(single_frame, text="Speed: --")
        self.speed_reading.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.load_reading = ttk.Label(single_frame, text="Load: --")
        self.load_reading.grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.temp_reading = ttk.Label(single_frame, text="Temperature: --")
        self.temp_reading.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.voltage_reading = ttk.Label(single_frame, text="Voltage: --")
        self.voltage_reading.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.current_reading = ttk.Label(single_frame, text="Current: --")
        self.current_reading.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Sync servo readings
        sync_frame = ttk.LabelFrame(readings_frame, text="Sync Mode - All Servos")
        sync_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create scrollable text for sync readings
        self.sync_readings_text = scrolledtext.ScrolledText(sync_frame, height=8, state=tk.DISABLED)
        self.sync_readings_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Monitor controls
        monitor_ctrl_frame = ttk.Frame(readings_frame)
        monitor_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_btn = ttk.Button(monitor_ctrl_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(monitor_ctrl_frame, text="Refresh Once", command=self.refresh_readings).pack(side=tk.LEFT, padx=5)
        ttk.Button(monitor_ctrl_frame, text="Clear Sync Readings", command=self.clear_sync_readings).pack(side=tk.LEFT, padx=5)
        
        # Log
        log_frame = ttk.LabelFrame(mon_frame, text="Activity Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)
    
    def create_settings_tab(self, notebook):
        """Create settings tab"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        
        # ID Management
        id_frame = ttk.LabelFrame(settings_frame, text="ID Management")
        id_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(id_frame, text="Current ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.old_id_var = tk.StringVar(value="0")       # Changed to 0
        ttk.Entry(id_frame, textvariable=self.old_id_var, width=8).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(id_frame, text="New ID:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.new_id_var = tk.StringVar(value="1")       # Changed to 1
        ttk.Entry(id_frame, textvariable=self.new_id_var, width=8).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Button(id_frame, text="Change ID", command=self.change_servo_id).grid(row=0, column=4, padx=5, pady=2)
        
        # Limits
        limits_frame = ttk.LabelFrame(settings_frame, text="Position Limits")
        limits_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(limits_frame, text="Min Position:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.min_pos_var = tk.StringVar(value=str(self.default_params['min_pos']))
        ttk.Entry(limits_frame, textvariable=self.min_pos_var, width=8).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(limits_frame, text="Max Position:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.max_pos_var = tk.StringVar(value=str(self.default_params['max_pos']))
        ttk.Entry(limits_frame, textvariable=self.max_pos_var, width=8).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Button(limits_frame, text="Set Limits", command=self.set_position_limits).grid(row=0, column=4, padx=5, pady=2)
        
        # Reset all defaults
        reset_frame = ttk.LabelFrame(settings_frame, text="Reset Functions")
        reset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(reset_frame, text="Reset All to Defaults", command=self.reset_all_defaults).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(reset_frame, text="Reset Connection Settings", command=self.reset_connection_defaults).grid(row=0, column=1, padx=5, pady=5)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.status_bar.config(text=message)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def connect_servo(self):
        """Connect to servo"""
        try:
            self.port_handler = PortHandler(self.device_name)
            self.packet_handler = sts(self.port_handler)
            
            if self.port_handler.openPort():
                if self.port_handler.setBaudRate(self.baudrate):
                    self.connected = True
                    self.status_label.config(text="Connected", foreground="green")
                    self.connect_btn.config(state=tk.DISABLED)
                    self.disconnect_btn.config(state=tk.NORMAL)
                    self.log_message("Connected to servo successfully")
                else:
                    self.log_message("Failed to set baudrate")
                    self.port_handler.closePort()
            else:
                self.log_message("Failed to open port")
        except Exception as e:
            self.log_message(f"Connection error: {str(e)}")
    
    def disconnect_servo(self):
        """Disconnect from servo"""
        if self.port_handler:
            self.monitoring = False
            self.port_handler.closePort()
            self.connected = False
            self.status_label.config(text="Disconnected", foreground="red")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.monitor_btn.config(text="Start Monitoring")
            self.log_message("Disconnected from servo")
    
    def set_active_servo(self):
        """Set the active servo ID"""
        try:
            self.current_servo_id = int(self.servo_id_var.get())
            self.log_message(f"Active servo set to ID: {self.current_servo_id}")
        except ValueError:
            messagebox.showerror("Error", "Invalid servo ID")
    
    def on_mode_change(self):
        """Handle control mode change"""
        self.control_mode = self.mode_var.get()
        
        if self.control_mode == "single":
            mode_text = "Mode: Single Servo Control"
            mode_color = "blue"
            self.log_message("Switched to Single Servo Control mode")
        else:
            servo_count = len(self.sync_servo_list)
            mode_text = f"Mode: Sync Control ({servo_count} servos)"
            mode_color = "green"
            if not self.sync_servo_list:
                messagebox.showwarning("Warning", "No servos in sync list. Please add servos in the Sync Operations tab.")
            self.log_message(f"Switched to Sync Control mode with {servo_count} servo(s)")
        
        # Update all mode indicators
        self.mode_status_label.config(text=mode_text, foreground=mode_color)
        if hasattr(self, 'ctrl_mode_label'):
            self.ctrl_mode_label.config(text=mode_text, foreground=mode_color)
        
        # Update monitoring if it's running
        if self.monitoring:
            self.log_message("Restarting monitoring for new mode")
    
    def ping_servo(self):
        """Ping the current servo"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            servo_id = int(self.servo_id_var.get())
            model_number, comm_result, error = self.packet_handler.ping(servo_id)
            
            if comm_result == COMM_SUCCESS and error == 0:
                self.log_message(f"Ping successful! Servo ID: {servo_id}, Model: {model_number}")
                messagebox.showinfo("Ping Result", f"Servo ID {servo_id} found!\nModel: {model_number}")
            else:
                self.log_message(f"Ping failed for ID {servo_id}")
                messagebox.showwarning("Ping Result", f"No response from servo ID {servo_id}")
        except ValueError:
            messagebox.showerror("Error", "Invalid servo ID")
        except Exception as e:
            self.log_message(f"Ping error: {str(e)}")
    
    def scan_servos(self, start_id, end_id):
        """Scan for servos in range"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        def scan_thread():
            # Clear previous results
            for item in self.servo_tree.get_children():
                self.servo_tree.delete(item)
            
            found_servos = []
            total_range = end_id - start_id + 1
            
            self.scan_progress['maximum'] = total_range
            self.scan_progress['value'] = 0
            
            for i, servo_id in enumerate(range(start_id, end_id + 1)):
                try:
                    model_number, comm_result, error = self.packet_handler.ping(servo_id)
                    
                    if comm_result == COMM_SUCCESS and error == 0:
                        found_servos.append({
                            'id': servo_id,
                            'model': model_number,
                            'status': 'Online'
                        })
                        
                        # Add to tree
                        self.servo_tree.insert('', tk.END, values=(servo_id, model_number, 'Online'))
                        self.log_message(f"Found servo at ID: {servo_id}, Model: {model_number}")
                    
                    self.scan_progress['value'] = i + 1
                    self.root.update_idletasks()
                    time.sleep(0.01)  # Small delay
                    
                except Exception as e:
                    self.log_message(f"Scan error at ID {servo_id}: {str(e)}")
            
            self.scan_progress['value'] = total_range
            self.log_message(f"Scan complete. Found {len(found_servos)} servo(s)")
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def quick_scan(self):
        """Quick scan (0-20)"""
        self.scan_servos(0, 20)
    
    def full_scan(self):
        """Full scan (0-253)"""
        self.scan_servos(0, 253)
    
    def custom_scan(self):
        """Custom range scan"""
        try:
            start_id = int(self.scan_start_var.get())
            end_id = int(self.scan_end_var.get())
            
            if start_id < 0 or end_id > 253 or start_id > end_id:
                messagebox.showerror("Error", "Invalid scan range")
                return
                
            self.scan_servos(start_id, end_id)
        except ValueError:
            messagebox.showerror("Error", "Invalid scan range values")
    
    def on_servo_select(self, event):
        """Handle servo selection from tree"""
        selection = self.servo_tree.selection()
        if selection:
            item = self.servo_tree.item(selection[0])
            servo_id = item['values'][0]
            self.servo_id_var.set(str(servo_id))
            self.current_servo_id = servo_id
            self.log_message(f"Selected servo ID: {servo_id}")
    
    def move_to_position(self):
        """Move servo to target position (single or sync mode)"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            target_pos = int(self.target_pos_var.get())
            speed = int(self.speed_var.get())
            acc = int(self.acc_var.get())
            
            if self.control_mode == "single":
                # Single servo mode - first ensure servo is in position mode
                comm_result, error = self.packet_handler.write1ByteTxRx(self.current_servo_id, 33, 0)  # STS_MODE = 33
                if comm_result != COMM_SUCCESS or error != 0:
                    self.log_message(f"Failed to set position mode for servo ID {self.current_servo_id}")
                    return
                
                # Now send position command
                comm_result, error = self.packet_handler.WritePosEx(self.current_servo_id, target_pos, speed, acc)
                
                if comm_result == COMM_SUCCESS and error == 0:
                    self.log_message(f"Moving servo ID {self.current_servo_id} to position {target_pos}")
                else:
                    self.log_message(f"Failed to move servo: {self.packet_handler.getTxRxResult(comm_result)}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    messagebox.showerror("Error", "No servos in sync list")
                    return
                
                # First ensure all servos are in position mode
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.write1ByteTxRx(servo_id, 33, 0)  # STS_MODE = 33
                        if comm_result != COMM_SUCCESS or error != 0:
                            self.log_message(f"Failed to set position mode for servo ID {servo_id}")
                    except Exception as e:
                        self.log_message(f"Error setting position mode for servo ID {servo_id}: {str(e)}")
                
                # Now send position commands to all servos
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.WritePosEx(servo_id, target_pos, speed, acc)
                        if comm_result == COMM_SUCCESS and error == 0:
                            success_count += 1
                            self.log_message(f"Moving servo ID {servo_id} to position {target_pos}")
                        else:
                            self.log_message(f"Failed to move servo ID {servo_id}: {self.packet_handler.getTxRxResult(comm_result)}")
                    except Exception as e:
                        self.log_message(f"Error moving servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    messagebox.showinfo("Success", f"Successfully moved {success_count}/{len(self.sync_servo_list)} servo(s)")
                
        except ValueError:
            messagebox.showerror("Error", "Invalid position values")
        except Exception as e:
            self.log_message(f"Move error: {str(e)}")
    
    def stop_servo(self):
        """Stop servo movement (single or sync mode)"""
        if not self.connected:
            return
        
        try:
            if self.control_mode == "single":
                # Single servo mode
                pos, speed, comm_result, error = self.packet_handler.ReadPosSpeed(self.current_servo_id)
                if comm_result == COMM_SUCCESS:
                    self.packet_handler.WritePosEx(self.current_servo_id, pos, 0, 0)
                    self.log_message(f"Stopped servo ID {self.current_servo_id}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    return
                
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        pos, speed, comm_result, error = self.packet_handler.ReadPosSpeed(servo_id)
                        if comm_result == COMM_SUCCESS:
                            self.packet_handler.WritePosEx(servo_id, pos, 0, 0)
                            self.log_message(f"Stopped servo ID {servo_id}")
                            success_count += 1
                    except Exception as e:
                        self.log_message(f"Error stopping servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    self.log_message(f"Stopped {success_count}/{len(self.sync_servo_list)} servo(s)")
                    
        except Exception as e:
            self.log_message(f"Stop error: {str(e)}")
    
    def enable_torque(self):
        """Enable torque (single or sync mode)"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            if self.control_mode == "single":
                # Single servo mode
                comm_result, error = self.packet_handler.write1ByteTxRx(self.current_servo_id, STS_TORQUE_ENABLE, 1)
                if comm_result == COMM_SUCCESS and error == 0:
                    self.log_message(f"Torque enabled for servo ID {self.current_servo_id}")
                else:
                    self.log_message(f"Failed to enable torque: {self.packet_handler.getTxRxResult(comm_result)}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    messagebox.showerror("Error", "No servos in sync list")
                    return
                
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE, 1)
                        if comm_result == COMM_SUCCESS and error == 0:
                            self.log_message(f"Torque enabled for servo ID {servo_id}")
                            success_count += 1
                        else:
                            self.log_message(f"Failed to enable torque for servo ID {servo_id}")
                    except Exception as e:
                        self.log_message(f"Error enabling torque for servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    messagebox.showinfo("Success", f"Enabled torque for {success_count}/{len(self.sync_servo_list)} servo(s)")
                    
        except Exception as e:
            self.log_message(f"Torque enable error: {str(e)}")
    
    def disable_torque(self):
        """Disable torque (single or sync mode)"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            if self.control_mode == "single":
                # Single servo mode
                comm_result, error = self.packet_handler.write1ByteTxRx(self.current_servo_id, STS_TORQUE_ENABLE, 0)
                if comm_result == COMM_SUCCESS and error == 0:
                    self.log_message(f"Torque disabled for servo ID {self.current_servo_id}")
                else:
                    self.log_message(f"Failed to disable torque: {self.packet_handler.getTxRxResult(comm_result)}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    messagebox.showerror("Error", "No servos in sync list")
                    return
                
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.write1ByteTxRx(servo_id, STS_TORQUE_ENABLE, 0)
                        if comm_result == COMM_SUCCESS and error == 0:
                            self.log_message(f"Torque disabled for servo ID {servo_id}")
                            success_count += 1
                        else:
                            self.log_message(f"Failed to disable torque for servo ID {servo_id}")
                    except Exception as e:
                        self.log_message(f"Error disabling torque for servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    messagebox.showinfo("Success", f"Disabled torque for {success_count}/{len(self.sync_servo_list)} servo(s)")
                    
        except Exception as e:
            self.log_message(f"Torque disable error: {str(e)}")
    
    def calibrate_center(self):
        """Calibrate servo center position"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            comm_result, error = self.packet_handler.write1ByteTxRx(self.current_servo_id, STS_TORQUE_ENABLE, 128)
            if comm_result == COMM_SUCCESS and error == 0:
                self.log_message(f"Center calibrated for servo ID {self.current_servo_id}")
                messagebox.showinfo("Calibration", "Center position calibrated successfully")
            else:
                self.log_message(f"Failed to calibrate: {self.packet_handler.getTxRxResult(comm_result)}")
        except Exception as e:
            self.log_message(f"Calibration error: {str(e)}")
    
    def enable_position_mode(self):
        """Enable position mode (single or sync mode)"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            if self.control_mode == "single":
                # Single servo mode - write 0 to STS_MODE to enable position mode
                comm_result, error = self.packet_handler.write1ByteTxRx(self.current_servo_id, 33, 0)  # STS_MODE = 33
                if comm_result == COMM_SUCCESS and error == 0:
                    self.log_message(f"Position mode enabled for servo ID {self.current_servo_id}")
                else:
                    self.log_message(f"Failed to enable position mode: {self.packet_handler.getTxRxResult(comm_result)}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    messagebox.showerror("Error", "No servos in sync list")
                    return
                
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.write1ByteTxRx(servo_id, 33, 0)  # STS_MODE = 33
                        if comm_result == COMM_SUCCESS and error == 0:
                            self.log_message(f"Position mode enabled for servo ID {servo_id}")
                            success_count += 1
                        else:
                            self.log_message(f"Failed to enable position mode for servo ID {servo_id}")
                    except Exception as e:
                        self.log_message(f"Error enabling position mode for servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    messagebox.showinfo("Success", f"Enabled position mode for {success_count}/{len(self.sync_servo_list)} servo(s)")
                    
        except Exception as e:
            self.log_message(f"Position mode error: {str(e)}")

    def enable_wheel_mode(self):
        """Enable wheel mode (single or sync mode)"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            if self.control_mode == "single":
                # Single servo mode
                comm_result, error = self.packet_handler.WheelMode(self.current_servo_id)
                if comm_result == COMM_SUCCESS and error == 0:
                    self.log_message(f"Wheel mode enabled for servo ID {self.current_servo_id}")
                else:
                    self.log_message(f"Failed to enable wheel mode: {self.packet_handler.getTxRxResult(comm_result)}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    messagebox.showerror("Error", "No servos in sync list")
                    return
                
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.WheelMode(servo_id)
                        if comm_result == COMM_SUCCESS and error == 0:
                            self.log_message(f"Wheel mode enabled for servo ID {servo_id}")
                            success_count += 1
                        else:
                            self.log_message(f"Failed to enable wheel mode for servo ID {servo_id}")
                    except Exception as e:
                        self.log_message(f"Error enabling wheel mode for servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    messagebox.showinfo("Success", f"Enabled wheel mode for {success_count}/{len(self.sync_servo_list)} servo(s)")
                    
        except Exception as e:
            self.log_message(f"Wheel mode error: {str(e)}")
    
    def set_wheel_speed(self):
        """Set wheel speed (single or sync mode)"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            speed = int(self.wheel_speed_var.get())
            acc = int(self.acc_var.get())
            
            if self.control_mode == "single":
                # Single servo mode
                comm_result, error = self.packet_handler.WriteSpec(self.current_servo_id, speed, acc)
                if comm_result == COMM_SUCCESS and error == 0:
                    self.log_message(f"Wheel speed set to {speed} for servo ID {self.current_servo_id}")
                else:
                    self.log_message(f"Failed to set wheel speed: {self.packet_handler.getTxRxResult(comm_result)}")
            else:
                # Sync mode
                if not self.sync_servo_list:
                    messagebox.showerror("Error", "No servos in sync list")
                    return
                
                success_count = 0
                for servo_id in self.sync_servo_list:
                    try:
                        comm_result, error = self.packet_handler.WriteSpec(servo_id, speed, acc)
                        if comm_result == COMM_SUCCESS and error == 0:
                            self.log_message(f"Wheel speed set to {speed} for servo ID {servo_id}")
                            success_count += 1
                        else:
                            self.log_message(f"Failed to set wheel speed for servo ID {servo_id}")
                    except Exception as e:
                        self.log_message(f"Error setting wheel speed for servo ID {servo_id}: {str(e)}")
                
                if success_count > 0:
                    messagebox.showinfo("Success", f"Set wheel speed for {success_count}/{len(self.sync_servo_list)} servo(s)")
                    
        except ValueError:
            messagebox.showerror("Error", "Invalid speed value")
        except Exception as e:
            self.log_message(f"Wheel speed error: {str(e)}")
    
    def change_servo_id(self):
        """Change servo ID"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            old_id = int(self.old_id_var.get())
            new_id = int(self.new_id_var.get())
            
            if new_id < 0 or new_id > 253:
                messagebox.showerror("Error", "Invalid ID range (0-253)")
                return
            
            # Confirm the change
            if not messagebox.askyesno("Confirm", f"Change servo ID from {old_id} to {new_id}?"):
                return
            
            # Unlock EPROM
            self.packet_handler.unLockEprom(old_id)
            
            # Change ID
            comm_result, error = self.packet_handler.write1ByteTxRx(old_id, STS_ID, new_id)
            
            if comm_result == COMM_SUCCESS and error == 0:
                # Verify the change
                new_id_read, comm_result2, error2 = self.packet_handler.read1ByteTxRx(new_id, STS_ID)
                if comm_result2 == COMM_SUCCESS and error2 == 0 and new_id_read == new_id:
                    self.log_message(f"Successfully changed servo ID from {old_id} to {new_id}")
                    messagebox.showinfo("Success", f"Servo ID changed to {new_id}")
                    self.servo_id_var.set(str(new_id))
                    self.current_servo_id = new_id
                else:
                    self.log_message("ID change verification failed")
            else:
                self.log_message(f"Failed to change ID: {self.packet_handler.getTxRxResult(comm_result)}")
            
            # Lock EPROM
            self.packet_handler.LockEprom(old_id)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid ID values")
        except Exception as e:
            self.log_message(f"ID change error: {str(e)}")
    
    def set_position_limits(self):
        """Set position limits"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        try:
            min_pos = int(self.min_pos_var.get())
            max_pos = int(self.max_pos_var.get())
            
            if min_pos >= max_pos or min_pos < 0 or max_pos > 4095:
                messagebox.showerror("Error", "Invalid position limits")
                return
            
            # Update scale ranges
            self.target_pos_scale.config(from_=min_pos, to=max_pos)
            self.log_message(f"Position limits set: {min_pos} - {max_pos}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid limit values")
    
    def refresh_readings(self):
        """Refresh servo readings once (single or sync mode)"""
        if not self.connected:
            return
        
        try:
            if self.control_mode == "single":
                self.refresh_single_servo_readings()
            else:
                self.refresh_sync_servo_readings()
        except Exception as e:
            self.log_message(f"Reading error: {str(e)}")
    
    def refresh_single_servo_readings(self):
        """Refresh single servo readings"""
        try:
            # Read position and speed
            pos, speed, comm_result, error = self.packet_handler.ReadPosSpeed(self.current_servo_id)
            if comm_result == COMM_SUCCESS and error == 0:
                self.pos_reading.config(text=f"Position: {pos}")
                self.speed_reading.config(text=f"Speed: {speed}")
            
            # Read load
            load, comm_result, error = self.packet_handler.ReadLoad(self.current_servo_id)
            if comm_result == COMM_SUCCESS and error == 0:
                self.load_reading.config(text=f"Load: {load}")
            
            # Read temperature
            temp, comm_result, error = self.packet_handler.ReadTemperature(self.current_servo_id)
            if comm_result == COMM_SUCCESS and error == 0:
                self.temp_reading.config(text=f"Temperature: {temp}°C")
            
            # Read voltage
            voltage, comm_result, error = self.packet_handler.ReadVoltage(self.current_servo_id)
            if comm_result == COMM_SUCCESS and error == 0:
                self.voltage_reading.config(text=f"Voltage: {voltage/10:.1f}V")
            
            # Read current
            current, comm_result, error = self.packet_handler.ReadCurrent(self.current_servo_id)
            if comm_result == COMM_SUCCESS and error == 0:
                self.current_reading.config(text=f"Current: {current}mA")
                
        except Exception as e:
            self.log_message(f"Single servo reading error: {str(e)}")
    
    def refresh_sync_servo_readings(self):
        """Refresh sync servo readings"""
        if not self.sync_servo_list:
            return
        
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            self.sync_readings_text.config(state=tk.NORMAL)
            self.sync_readings_text.insert(tk.END, f"\n[{timestamp}] Sync Servo Readings:\n")
            self.sync_readings_text.insert(tk.END, "="*60 + "\n")
            
            for servo_id in self.sync_servo_list:
                try:
                    # Read position and speed
                    pos, speed, comm_result, error = self.packet_handler.ReadPosSpeed(servo_id)
                    pos_str = f"{pos:4d}" if comm_result == COMM_SUCCESS and error == 0 else "----"
                    speed_str = f"{speed:4d}" if comm_result == COMM_SUCCESS and error == 0 else "----"
                    
                    # Read load
                    load, comm_result, error = self.packet_handler.ReadLoad(servo_id)
                    load_str = f"{load:4d}" if comm_result == COMM_SUCCESS and error == 0 else "----"
                    
                    # Read temperature
                    temp, comm_result, error = self.packet_handler.ReadTemperature(servo_id)
                    temp_str = f"{temp:3d}°C" if comm_result == COMM_SUCCESS and error == 0 else "----"
                    
                    # Read voltage
                    voltage, comm_result, error = self.packet_handler.ReadVoltage(servo_id)
                    voltage_str = f"{voltage/10:4.1f}V" if comm_result == COMM_SUCCESS and error == 0 else "----"
                    
                    # Read current
                    current, comm_result, error = self.packet_handler.ReadCurrent(servo_id)
                    current_str = f"{current:4d}mA" if comm_result == COMM_SUCCESS and error == 0 else "----"
                    
                    reading_line = f"ID {servo_id:3d}: Pos={pos_str} Spd={speed_str} Load={load_str} Temp={temp_str} Volt={voltage_str} Cur={current_str}\n"
                    self.sync_readings_text.insert(tk.END, reading_line)
                    
                except Exception as e:
                    self.sync_readings_text.insert(tk.END, f"ID {servo_id:3d}: Error - {str(e)}\n")
            
            self.sync_readings_text.insert(tk.END, "\n")
            self.sync_readings_text.see(tk.END)
            self.sync_readings_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.log_message(f"Sync servo reading error: {str(e)}")
    
    def clear_sync_readings(self):
        """Clear sync readings display"""
        self.sync_readings_text.config(state=tk.NORMAL)
        self.sync_readings_text.delete(1.0, tk.END)
        self.sync_readings_text.config(state=tk.DISABLED)
    
    def toggle_monitoring(self):
        """Start/stop continuous monitoring"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        if self.monitoring:
            self.monitoring = False
            self.monitor_btn.config(text="Start Monitoring")
            self.log_message("Monitoring stopped")
        else:
            self.monitoring = True
            self.monitor_btn.config(text="Stop Monitoring")
            self.log_message("Monitoring started")
            threading.Thread(target=self.monitoring_loop, daemon=True).start()
    
    def monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring and self.connected:
            self.refresh_readings()
            time.sleep(0.05)  # Update every second
    
    # Reset Functions
    def reset_control_defaults(self):
        """Reset control parameters to defaults"""
        self.target_pos_var.set(str(self.default_params['position']))
        self.speed_var.set(str(self.default_params['speed']))
        self.acc_var.set(str(self.default_params['acceleration']))
        self.wheel_speed_var.set(str(self.default_params['wheel_speed']))
        
        # Update scales
        self.target_pos_scale.set(self.default_params['position'])
        self.speed_scale.set(self.default_params['speed'])
        self.acc_scale.set(self.default_params['acceleration'])
        self.wheel_speed_scale.set(self.default_params['wheel_speed'])
        
        self.log_message("Control parameters reset to defaults")
    
    def reset_sync_defaults(self):
        """Reset sync operation parameters to defaults"""
        # Since sync now uses the same controls as single mode, just reset control defaults
        self.reset_control_defaults()
        self.log_message("Sync parameters reset to defaults")
    
    def reset_scan_defaults(self):
        """Reset scan parameters to defaults"""
        self.scan_start_var.set(str(self.default_params['scan_start']))
        self.scan_end_var.set(str(self.default_params['scan_end']))
        self.log_message("Scan parameters reset to defaults")
    
    def reset_connection_defaults(self):
        """Reset connection parameters to defaults"""
        self.servo_id_var.set(str(self.default_params['servo_id']))
        self.current_servo_id = self.default_params['servo_id']
        self.log_message("Connection parameters reset to defaults")
    
    def reset_all_defaults(self):
        """Reset all parameters to defaults"""
        # Control parameters
        self.reset_control_defaults()
        
        # Sync parameters
        self.reset_sync_defaults()
        
        # Scan parameters
        self.reset_scan_defaults()
        
        # Connection parameters
        self.reset_connection_defaults()
        
        # Position limits
        self.min_pos_var.set(str(self.default_params['min_pos']))
        self.max_pos_var.set(str(self.default_params['max_pos']))
        self.target_pos_scale.config(from_=self.default_params['min_pos'], to=self.default_params['max_pos'])
        
        # ID change settings
        self.old_id_var.set("0")            # Changed to 0
        self.new_id_var.set("1")            # Changed to 1
        
        # Clear sync servo list
        self.sync_servo_list.clear()
        self.update_sync_servo_display()
        
        self.log_message("All parameters reset to defaults")
        messagebox.showinfo("Reset Complete", "All parameters have been reset to default values")
    
    # Sync Operation Functions
    def add_servo_to_sync(self):
        """Add servo ID to sync operation list"""
        try:
            servo_id = int(self.add_servo_var.get())
            if servo_id < 0 or servo_id > 253:
                messagebox.showerror("Error", "Invalid servo ID (0-253)")
                return
            
            if servo_id not in self.sync_servo_list:
                self.sync_servo_list.append(servo_id)
                self.sync_servo_list.sort()
                self.update_sync_servo_display()
                self.log_message(f"Added servo ID {servo_id} to sync list")
            else:
                messagebox.showwarning("Warning", f"Servo ID {servo_id} already in list")
        except ValueError:
            messagebox.showerror("Error", "Invalid servo ID")
    
    def clear_servo_sync_list(self):
        """Clear the sync servo list"""
        self.sync_servo_list.clear()
        self.update_sync_servo_display()
        self.log_message("Sync servo list cleared")
    
    def auto_add_found_servos(self):
        """Automatically scan for servos and add them to sync list"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        # Show confirmation dialog
        if not messagebox.askyesno("Auto Scan & Add", 
                                  "This will perform a full servo scan (0-253) and add all found servos to the sync list.\n\nThis may take a few seconds. Continue?"):
            return
        
        self.log_message("Starting auto scan and add operation...")
        
        # Start the scan and add process in a thread
        def auto_scan_and_add_thread():
            try:
                # Disable scan buttons during operation
                self.quick_scan_btn.config(state='disabled')
                self.full_scan_btn.config(state='disabled')
                self.custom_scan_btn.config(state='disabled')
                self.sync_auto_add_button.config(state='disabled')
                self.is_scanning = True
                
                # Clear previous results
                for item in self.servo_tree.get_children():
                    self.servo_tree.delete(item)
                
                found_servos = []
                total_range = 254  # 0 to 253
                
                self.scan_progress['maximum'] = total_range
                self.scan_progress['value'] = 0
                self.sync_scan_progress['maximum'] = total_range
                self.sync_scan_progress['value'] = 0
                self.sync_scan_percentage_label.config(text="0%")
                
                self.log_message("Scanning all servo IDs (0-253)...")
                
                # Scan all IDs from 0 to 253
                for i, servo_id in enumerate(range(0, 254)):
                    try:
                        # Calculate and display percentage
                        percentage = ((i + 1) * 100) // total_range
                        self.log_message(f"Scanning ID {servo_id}... ({percentage}% complete)")
                        
                        model_number, comm_result, error = self.packet_handler.ping(servo_id)
                        
                        if comm_result == COMM_SUCCESS and error == 0:
                            found_servos.append({
                                'id': servo_id,
                                'model': model_number,
                                'status': 'Online'
                            })
                            
                            # Add to tree
                            self.servo_tree.insert('', tk.END, values=(servo_id, model_number, 'Online'))
                            self.log_message(f"Found servo at ID: {servo_id}, Model: {model_number}")
                        
                        self.scan_progress['value'] = i + 1
                        self.sync_scan_progress['value'] = i + 1
                        self.sync_scan_percentage_label.config(text=f"{percentage}%")
                        self.root.update_idletasks()
                        time.sleep(0.01)  # Small delay
                        
                    except Exception as e:
                        self.log_message(f"Scan error at ID {servo_id}: {str(e)}")
                
                self.scan_progress['value'] = total_range
                self.sync_scan_progress['value'] = total_range
                self.sync_scan_percentage_label.config(text="100%")
                self.log_message(f"Scan complete (100%). Found {len(found_servos)} servo(s)")
                
                # Now add all found servos to sync list
                if found_servos:
                    added_count = 0
                    skipped_count = 0
                    
                    for servo_info in found_servos:
                        servo_id = servo_info['id']
                        if servo_id not in self.sync_servo_list:
                            self.sync_servo_list.append(servo_id)
                            added_count += 1
                            self.log_message(f"Auto-added servo ID {servo_id} to sync list")
                        else:
                            skipped_count += 1
                    
                    if added_count > 0:
                        self.sync_servo_list.sort()
                        self.update_sync_servo_display()
                        
                        # Provide detailed feedback
                        if skipped_count > 0:
                            message = f"Scan complete!\n\nFound {len(found_servos)} servo(s)\nAdded {added_count} new servo(s) to sync list\n{skipped_count} servo(s) were already in the list"
                        else:
                            message = f"Scan complete!\n\nFound {len(found_servos)} servo(s)\nAdded all {added_count} servo(s) to sync list"
                        
                        messagebox.showinfo("Auto Scan & Add Complete", message)
                        self.log_message(f"Auto scan & add complete: {added_count} added, {skipped_count} skipped")
                    else:
                        if skipped_count > 0:
                            messagebox.showinfo("Auto Scan & Add Complete", 
                                               f"Found {len(found_servos)} servo(s)\nAll discovered servo(s) were already in the sync list")
                        else:
                            messagebox.showinfo("Auto Scan & Add Complete", 
                                               f"Found {len(found_servos)} servo(s)\nNo new servos to add to sync list")
                else:
                    messagebox.showwarning("Auto Scan & Add Complete", 
                                         "No servos found during the scan.\nPlease check your connections and try again.")
                    
            except Exception as e:
                self.log_message(f"Auto scan and add error: {str(e)}")
                messagebox.showerror("Error", f"Auto scan and add failed: {str(e)}")
            finally:
                # Reset both progress displays
                self.scan_progress['value'] = 0
                self.sync_scan_progress['value'] = 0
                self.sync_scan_percentage_label.config(text="0%")
                
                # Re-enable scanning buttons
                self.quick_scan_btn.config(state='normal')
                self.full_scan_btn.config(state='normal')
                self.custom_scan_btn.config(state='normal')
                self.sync_auto_add_button.config(state='normal')
                self.is_scanning = False
        
        # Start the operation in a background thread
        threading.Thread(target=auto_scan_and_add_thread, daemon=True).start()
    
    def update_sync_servo_display(self):
        """Update the sync servo list display"""
        self.sync_servo_label.config(text=str(self.sync_servo_list))
        
        # Update mode status if needed
        if self.control_mode == "sync":
            self.mode_status_label.config(text=f"Mode: Sync Control ({len(self.sync_servo_list)} servos)")
            
        self.log_message(f"Sync servo list updated: {self.sync_servo_list}")
    
    def sync_write_position(self):
        """Perform synchronous write to all servos in list"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        if not self.sync_servo_list:
            messagebox.showerror("Error", "No servos in sync list")
            return
        
        try:
            target_pos = int(self.target_pos_var.get())
            speed = int(self.speed_var.get())
            acc = int(self.acc_var.get())
            
            # First ensure all servos are in position mode
            self.log_message("Setting all servos to position mode for sync write...")
            for servo_id in self.sync_servo_list:
                try:
                    comm_result, error = self.packet_handler.write1ByteTxRx(servo_id, 33, 0)  # STS_MODE = 33
                    if comm_result == COMM_SUCCESS and error == 0:
                        self.log_message(f"Position mode enabled for servo ID {servo_id}")
                    else:
                        self.log_message(f"Failed to set position mode for servo ID {servo_id}")
                except Exception as e:
                    self.log_message(f"Error setting position mode for servo ID {servo_id}: {str(e)}")
            
            # Initialize group sync write
            if hasattr(self.packet_handler, 'groupSyncWrite'):
                self.packet_handler.groupSyncWrite.clearParam()
            
            success_count = 0
            for servo_id in self.sync_servo_list:
                try:
                    # Add parameters for each servo
                    result = self.packet_handler.SyncWritePosEx(servo_id, target_pos, speed, acc)
                    if result:
                        success_count += 1
                        self.log_message(f"Added sync write params for servo ID {servo_id}")
                    else:
                        self.log_message(f"Failed to add sync write params for servo ID {servo_id}")
                except Exception as e:
                    self.log_message(f"Error adding servo ID {servo_id}: {str(e)}")
            
            if success_count > 0:
                # Execute sync write
                try:
                    comm_result = self.packet_handler.groupSyncWrite.txPacket()
                    if comm_result == COMM_SUCCESS:
                        self.log_message(f"Sync write successful to {success_count} servo(s)")
                        messagebox.showinfo("Success", f"Sync write completed for {success_count} servo(s)")
                    else:
                        self.log_message(f"Sync write failed: {self.packet_handler.getTxRxResult(comm_result)}")
                    
                    # Clear parameters
                    self.packet_handler.groupSyncWrite.clearParam()
                except Exception as e:
                    self.log_message(f"Sync write execution error: {str(e)}")
            else:
                messagebox.showerror("Error", "No servos successfully added to sync write")
                
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values")
        except Exception as e:
            self.log_message(f"Sync write error: {str(e)}")
    
    def sync_stop_all(self):
        """Stop all servos in sync list"""
        if not self.connected or not self.sync_servo_list:
            return
        
        try:
            # Read current positions and set them as targets with zero speed
            for servo_id in self.sync_servo_list:
                try:
                    pos, speed, comm_result, error = self.packet_handler.ReadPosSpeed(servo_id)
                    if comm_result == COMM_SUCCESS:
                        self.packet_handler.WritePosEx(servo_id, pos, 0, 0)
                        self.log_message(f"Stopped servo ID {servo_id}")
                except Exception as e:
                    self.log_message(f"Error stopping servo ID {servo_id}: {str(e)}")
        except Exception as e:
            self.log_message(f"Sync stop error: {str(e)}")
    
    def sync_read_pos_speed(self):
        """Perform synchronous read of position and speed"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        if not self.sync_servo_list:
            messagebox.showerror("Error", "No servos in sync list")
            return
        
        try:
            from ..sdk import GroupSyncRead, STS_PRESENT_POSITION_L
            
            # Initialize group sync read
            groupSyncRead = GroupSyncRead(self.packet_handler, STS_PRESENT_POSITION_L, 4)
            
            # Add parameters for each servo
            for servo_id in self.sync_servo_list:
                result = groupSyncRead.addParam(servo_id)
                if not result:
                    self.log_message(f"Failed to add sync read param for servo ID {servo_id}")
            
            # Execute sync read
            comm_result = groupSyncRead.txRxPacket()
            if comm_result != COMM_SUCCESS:
                self.log_message(f"Sync read failed: {self.packet_handler.getTxRxResult(comm_result)}")
                return
            
            # Display results
            self.display_sync_results("Position/Speed Read Results:", groupSyncRead, ['Position', 'Speed'])
            
        except Exception as e:
            self.log_message(f"Sync read error: {str(e)}")
    
    def sync_read_all_data(self):
        """Perform synchronous read of all data"""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to servo")
            return
        
        if not self.sync_servo_list:
            messagebox.showerror("Error", "No servos in sync list")
            return
        
        try:
            from ..sdk import GroupSyncRead, STS_PRESENT_POSITION_L
            
            # Initialize group sync read for extended data
            groupSyncRead = GroupSyncRead(self.packet_handler, STS_PRESENT_POSITION_L, 24)
            
            # Add parameters for each servo
            for servo_id in self.sync_servo_list:
                result = groupSyncRead.addParam(servo_id)
                if not result:
                    self.log_message(f"Failed to add sync read param for servo ID {servo_id}")
            
            # Execute sync read
            comm_result = groupSyncRead.txRxPacket()
            if comm_result != COMM_SUCCESS:
                self.log_message(f"Sync read all data failed: {self.packet_handler.getTxRxResult(comm_result)}")
                return
            
            # Display results
            self.display_sync_results("All Data Read Results:", groupSyncRead, 
                                    ['Position', 'Speed', 'Load', 'Voltage', 'Temperature', 'Current', 'Status'])
            
        except Exception as e:
            self.log_message(f"Sync read all data error: {str(e)}")
    
    def display_sync_results(self, title, groupSyncRead, data_types):
        """Display synchronous read results"""
        try:
            from ..sdk import STS_PRESENT_POSITION_L, STS_PRESENT_SPEED_L, STS_PRESENT_LOAD_L
            
            self.sync_results_text.config(state=tk.NORMAL)
            self.sync_results_text.insert(tk.END, f"\n{title}\n")
            self.sync_results_text.insert(tk.END, "="*50 + "\n")
            
            for servo_id in self.sync_servo_list:
                data_available, error = groupSyncRead.isAvailable(servo_id, STS_PRESENT_POSITION_L, 4)
                
                if data_available:
                    position = groupSyncRead.getData(servo_id, STS_PRESENT_POSITION_L, 2)
                    speed = groupSyncRead.getData(servo_id, STS_PRESENT_SPEED_L, 2)
                    
                    result_line = f"ID {servo_id:3d}: Pos={position:4d}, Speed={speed:4d}"
                    
                    if len(data_types) > 2:  # Extended data
                        try:
                            load = groupSyncRead.getData(servo_id, STS_PRESENT_LOAD_L, 2)
                            result_line += f", Load={load:4d}"
                        except:
                            pass
                    
                    self.sync_results_text.insert(tk.END, result_line + "\n")
                else:
                    self.sync_results_text.insert(tk.END, f"ID {servo_id:3d}: No data available\n")
                    if error != 0:
                        self.sync_results_text.insert(tk.END, f"       Error: {self.packet_handler.getRxPacketError(error)}\n")
            
            self.sync_results_text.insert(tk.END, "\n")
            self.sync_results_text.see(tk.END)
            self.sync_results_text.config(state=tk.DISABLED)
            
            groupSyncRead.clearParam()
            self.log_message(f"Sync read completed for {len(self.sync_servo_list)} servo(s)")
            
        except Exception as e:
            self.log_message(f"Display sync results error: {str(e)}")
    
    def clear_sync_results(self):
        """Clear sync results display"""
        self.sync_results_text.config(state=tk.NORMAL)
        self.sync_results_text.delete(1.0, tk.END)
        self.sync_results_text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = STServoGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
