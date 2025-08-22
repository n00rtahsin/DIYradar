#!/usr/bin/env python3
"""
Ultrasonic Radar Visualizer
A complete Python program for visualizing live ultrasonic sensor data from Arduino
in a polar radar display with smooth animation and robust error handling.
"""

import argparse
import csv
import sys
import time
import threading
from collections import deque
from datetime import datetime
from typing import Optional, Tuple, List

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Wedge
import numpy as np
import serial

# ============================================================================
# CONFIGURATION - Edit these settings as needed
# ============================================================================

PORT = "COM7"                    # Default serial port
BAUD = 9600                     # Serial baud rate
MAX_RANGE_CM = 1200              # Maximum radar range in cm (increased for your data)
FADE_SWEEPS = 4                 # Number of sweep trails to keep
READ_TIMEOUT_S = 0.1            # Serial read timeout
LOG_TO_CSV = False              # Enable CSV logging
CSV_FILE = "radar_log.csv"      # CSV log file name
DARK_THEME = True               # Use dark theme
ANIMATION_INTERVAL_MS = 50      # Animation update interval

# Derived constants
RANGE_RINGS_INTERVAL = 50       # Distance between range rings
DATA_TIMEOUT_S = 1.0           # Show "NO DATA" after this timeout
MAX_QUEUE_SIZE = 1000          # Maximum data queue size

# ============================================================================
# GLOBAL STATE
# ============================================================================

class RadarState:
    def __init__(self):
        self.serial_conn: Optional[serial.Serial] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.data_queue = deque(maxlen=MAX_QUEUE_SIZE)
        self.sweep_history = deque(maxlen=FADE_SWEEPS)
        self.last_data_time = 0
        self.last_angle = 0
        self.running = True
        self.csv_writer = None
        self.csv_file_handle = None

state = RadarState()

# ============================================================================
# SERIAL DATA READER
# ============================================================================

def serial_reader_thread():
    """Background thread that reads data from Arduino and queues valid points."""
    print(f"[*] Serial reader thread started on {PORT}")
    
    angle_counter = 0
    buffer = ""  # Buffer to accumulate partial data
    
    while state.running:
        try:
            if not state.serial_conn or not state.serial_conn.is_open:
                time.sleep(0.1)
                continue
            
            # Read available bytes (not lines, since Arduino doesn't send proper line breaks)
            bytes_waiting = state.serial_conn.in_waiting
            if bytes_waiting > 0:
                try:
                    # Read raw bytes and decode
                    raw_data = state.serial_conn.read(bytes_waiting)
                    new_data = raw_data.decode('utf-8', errors='ignore')
                    buffer += new_data
                    
                    print(f"[DEBUG] Read {len(new_data)} chars, buffer now {len(buffer)} chars")
                    
                    # Process complete comma-separated values
                    while ',' in buffer:
                        # Find the next comma
                        comma_pos = buffer.find(',')
                        value_str = buffer[:comma_pos].strip()
                        buffer = buffer[comma_pos + 1:]  # Remove processed part
                        
                        if not value_str:
                            continue
                            
                        try:
                            # Parse as float to handle decimals
                            distance = float(value_str)
                            
                            # Convert to integer cm (round decimals)
                            distance_cm = int(round(distance))
                            
                            # Generate sweep angle (0-180 back and forth)
                            sweep_pos = angle_counter % 360
                            if sweep_pos > 180:
                                angle = 360 - sweep_pos
                            else:
                                angle = sweep_pos
                            
                            print(f"[DEBUG] Parsed: {value_str} -> angle={angle}°, distance={distance_cm}cm")
                            
                            # Validate distance
                            if distance_cm < 2:
                                print(f"[DEBUG] Distance too small: {distance_cm}")
                                angle_counter += 1
                                continue
                            if distance_cm > 2000:
                                print(f"[DEBUG] Distance too large: {distance_cm}, clamping to 2000")
                                distance_cm = 2000
                                
                            # Queue valid data point
                            timestamp = time.time()
                            state.data_queue.append((timestamp, angle, distance_cm))
                            state.last_data_time = timestamp
                            state.last_angle = angle
                            print(f"[DEBUG] ✓ Queued: {angle}°, {distance_cm}cm")
                            
                            # Log to CSV if enabled
                            if state.csv_writer:
                                state.csv_writer.writerow([
                                    datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                                    angle,
                                    distance_cm
                                ])
                            
                            angle_counter += 1
                            
                        except ValueError as e:
                            print(f"[DEBUG] Parse error for '{value_str}': {e}")
                            continue
                    
                    # Keep buffer reasonable size
                    if len(buffer) > 1000:
                        buffer = buffer[-500:]  # Keep last 500 chars
                        
                except Exception as e:
                    print(f"[DEBUG] Read error: {e}")
                    continue
                    
            else:
                # No data waiting, small delay
                time.sleep(0.01)
                
        except serial.SerialException:
            if state.running:
                print("[!] Serial connection lost")
            break
        except Exception as e:
            if state.running:
                print(f"[!] Reader thread error: {e}")
            break
    
   
                
        except serial.SerialException:
            # Connection lost
            if state.running:
                print("[!] Serial connection lost")
            break
        except Exception as e:
            if state.running:
                print(f"[!] Reader thread error: {e}")
            break
    
    print("[*] Serial reader thread stopped")

# ============================================================================
# SERIAL CONNECTION MANAGEMENT
# ============================================================================

def open_serial_connection(port: str, baud: int) -> bool:
    """Open serial connection with proper error handling."""
    try:
        print(f"[*] Opening serial port {port} at {baud} baud...")
        state.serial_conn = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=READ_TIMEOUT_S,
            write_timeout=1.0
        )
        
        # Wait for Arduino to reset
        print("[*] Waiting for Arduino to initialize...")
        time.sleep(2)
        
        # Clear any initial garbage
        state.serial_conn.flushInput()
        
        print(f"[*] Serial connection established on {port}")
        
        # Test for immediate data
        print("[*] Testing for incoming data...")
        bytes_available = state.serial_conn.in_waiting
        print(f"[*] Bytes in buffer: {bytes_available}")
        
        if bytes_available > 0:
            # Read and show sample data
            sample_data = state.serial_conn.read(min(100, bytes_available))
            sample_str = sample_data.decode('utf-8', errors='ignore')
            print(f"[*] Sample data: '{sample_str}'")
            print(f"[*] Your Arduino is sending decimal comma-separated values - perfect!")
        else:
            print("[*] No immediate data, but that's OK - will keep trying...")
            
        return True
        
    except serial.SerialException as e:
        error_msg = str(e).lower()
        print(f"[!] Failed to open serial port {port}: {e}")
        
        if "access is denied" in error_msg or "permission denied" in error_msg:
            print("[!] Port is busy. Try these solutions:")
            print("    - Close Arduino Serial Monitor")
            print("    - Close other applications using the port")
            print("    - Check if another instance of this program is running")
        elif "could not open port" in error_msg or "no such file" in error_msg:
            print("[!] Port not found. Try these solutions:")
            print("    - Check if Arduino is connected")
            print("    - Verify the correct COM port in Device Manager")
            print("    - Try different ports like COM3, COM4, COM5, etc.")
        
        return False
    except Exception as e:
        print(f"[!] Unexpected error opening serial port: {e}")
        return False

def close_serial_connection():
    """Safely close serial connection."""
    if state.serial_conn and state.serial_conn.is_open:
        try:
            state.serial_conn.close()
            print("[*] Serial connection closed")
        except Exception as e:
            print(f"[!] Error closing serial connection: {e}")

# ============================================================================
# CSV LOGGING
# ============================================================================

def setup_csv_logging():
    """Initialize CSV logging if enabled."""
    if not LOG_TO_CSV:
        return
        
    try:
        state.csv_file_handle = open(CSV_FILE, 'w', newline='')
        state.csv_writer = csv.writer(state.csv_file_handle)
        state.csv_writer.writerow(['timestamp', 'angle_deg', 'distance_cm'])
        print(f"[*] CSV logging enabled: {CSV_FILE}")
    except Exception as e:
        print(f"[!] Failed to setup CSV logging: {e}")
        state.csv_writer = None

def close_csv_logging():
    """Close CSV file if open."""
    if state.csv_file_handle:
        try:
            state.csv_file_handle.close()
            print("[*] CSV file closed")
        except Exception as e:
            print(f"[!] Error closing CSV file: {e}")

# ============================================================================
# RADAR VISUALIZATION
# ============================================================================

def process_data_queue():
    """Process queued data points and update sweep history."""
    if not state.data_queue:
        return
        
    # Group data points by sweep direction
    current_sweep = []
    
    while state.data_queue:
        timestamp, angle, distance = state.data_queue.popleft()
        current_sweep.append((angle, distance, timestamp))
    
    if current_sweep:
        # Sort by angle to ensure proper sweep order
        current_sweep.sort(key=lambda x: x[0])
        state.sweep_history.append(current_sweep)

def polar_to_cartesian(angle_deg: float, distance: float) -> Tuple[float, float]:
    """Convert polar coordinates to cartesian for plotting."""
    # Convert to matplotlib polar convention (0° at top, clockwise)
    angle_rad = np.radians(90 - angle_deg)
    x = distance * np.cos(angle_rad)
    y = distance * np.sin(angle_rad)
    return x, y

def update_plot(frame):
    """Animation update function."""
    ax.clear()
    
    # Process new data
    process_data_queue()
    
    # Set up polar plot appearance
    if DARK_THEME:
        ax.set_facecolor('black')
        text_color = 'white'
        grid_color = 'gray'
        sweep_color = 'lime'
    else:
        ax.set_facecolor('white')
        text_color = 'black'
        grid_color = 'gray'
        sweep_color = 'red'
    
    # Set axis limits and appearance
    ax.set_xlim(-MAX_RANGE_CM, MAX_RANGE_CM)
    ax.set_ylim(-MAX_RANGE_CM, MAX_RANGE_CM)
    ax.set_aspect('equal')
    ax.grid(True, color=grid_color, alpha=0.3)
    
    # Draw range rings
    for radius in range(RANGE_RINGS_INTERVAL, MAX_RANGE_CM + 1, RANGE_RINGS_INTERVAL):
        circle = plt.Circle((0, 0), radius, fill=False, color=grid_color, alpha=0.3, linewidth=0.5)
        ax.add_patch(circle)
        
        # Add range labels
        ax.text(radius * 0.707, radius * 0.707, f'{radius}cm', 
               fontsize=8, color=text_color, alpha=0.6)
    
    # Draw angle lines
    for angle in range(0, 181, 30):
        x, y = polar_to_cartesian(angle, MAX_RANGE_CM)
        ax.plot([0, x], [0, y], color=grid_color, alpha=0.3, linewidth=0.5)
        
        # Add angle labels
        label_x, label_y = polar_to_cartesian(angle, MAX_RANGE_CM * 1.1)
        ax.text(label_x, label_y, f'{angle}°', fontsize=8, color=text_color, 
               alpha=0.6, ha='center', va='center')
    
    # Plot sweep history with fading effect
    if state.sweep_history:
        for i, sweep in enumerate(state.sweep_history):
            # Calculate alpha for fading effect (newest is most opaque)
            alpha = (i + 1) / len(state.sweep_history) * 0.8
            
            # Plot points in this sweep
            for angle, distance, timestamp in sweep:
                if distance <= MAX_RANGE_CM:
                    x, y = polar_to_cartesian(angle, distance)
                    color = sweep_color if i == len(state.sweep_history) - 1 else 'cyan'
                    ax.plot(x, y, 'o', color=color, alpha=alpha, markersize=2)
    
    # Draw sweep arm at current angle
    if time.time() - state.last_data_time < DATA_TIMEOUT_S:
        arm_x, arm_y = polar_to_cartesian(state.last_angle, MAX_RANGE_CM)
        ax.plot([0, arm_x], [0, arm_y], color=sweep_color, alpha=0.8, linewidth=2)
    
    # Status text
    current_time = time.time()
    if current_time - state.last_data_time > DATA_TIMEOUT_S:
        ax.text(0, MAX_RANGE_CM * 0.9, "NO DATA", fontsize=16, color='red',
               ha='center', va='center', weight='bold')
    
    # Remove axis ticks and labels for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

# ============================================================================
# CLEANUP AND SHUTDOWN
# ============================================================================

def cleanup():
    """Clean shutdown of all resources."""
    print("[*] Shutting down...")
    
    # Stop background thread
    state.running = False
    if state.reader_thread and state.reader_thread.is_alive():
        state.reader_thread.join(timeout=1.0)
    
    # Close connections
    close_serial_connection()
    close_csv_logging()
    
    print("[*] Cleanup complete")

def on_close(event):
    """Handle window close event."""
    cleanup()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ultrasonic Radar Visualizer")
    parser.add_argument("--port", default=PORT, help=f"Serial port (default: {PORT})")
    parser.add_argument("--baud", type=int, default=BAUD, help=f"Baud rate (default: {BAUD})")
    return parser.parse_args()

def main():
    """Main program entry point."""
    global ax, fig, anim
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Print system info
    print("=" * 50)
    print("Ultrasonic Radar Visualizer")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Matplotlib backend: {plt.get_backend()}")
    print(f"Target port: {args.port}")
    print(f"Baud rate: {args.baud}")
    print("=" * 50)
    
    # Set matplotlib backend to TkAgg for proper blocking behavior
    try:
        plt.switch_backend('TkAgg')
    except ImportError:
        print("[!] TkAgg backend not available, using default")
    
    # Setup CSV logging
    setup_csv_logging()
    
    # Open serial connection
    if not open_serial_connection(args.port, args.baud):
        print("[!] Failed to establish serial connection. Exiting.")
        return 1
    
    try:
        # Start background reader thread
        state.reader_thread = threading.Thread(target=serial_reader_thread, daemon=True)
        state.reader_thread.start()
        
        # Setup matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.canvas.manager.set_window_title("Ultrasonic Radar Visualizer")
        
        # Apply theme
        if DARK_THEME:
            fig.patch.set_facecolor('black')
        
        # Setup animation
        anim = animation.FuncAnimation(
            fig, update_plot, interval=ANIMATION_INTERVAL_MS, 
            cache_frame_data=False, blit=False
        )
        
        # Handle window close
        fig.canvas.mpl_connect('close_event', on_close)
        
        print("[*] Radar visualization started. Close window to exit.")
        print("[*] Waiting for data from Arduino...")
        
        # Show plot (this blocks until window is closed)
        plt.tight_layout()
        plt.show()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user")
        return 0
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return 1
    finally:
        cleanup()

if __name__ == "__main__":
    sys.exit(main())