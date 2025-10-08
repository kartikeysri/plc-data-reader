import serial
import time
import yaml
import sys
import threading
import re
from datetime import datetime
import os
from dataclasses import dataclass
from collections import deque


@dataclass
class SensorReading:
    temperature: float
    pressure: float
    speed: float
    timestamp: datetime
    raw_data: str


# Global variables for data storage and connection status
serial_connection = None
is_running = False
last_reading = None
last_reading_timestamp = None
data_history = deque(maxlen=100)
is_connected = False
last_data_received = None
stop_event = threading.Event()

# Configuration variables
config = None
max_silence_time = 10
health_check_interval = 5
connection_retry_interval = 5


def load_config(config_file: str):
    global config, max_silence_time, health_check_interval, connection_retry_interval
    
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            print(f"Configuration loaded from {config_file}")
            
            # Load health monitoring configuration
            health_config = config.get('reader', {}).get('health', {})
            max_silence_time = health_config.get('max_silence_time', 10)
            health_check_interval = health_config.get('check_interval', 5)
            connection_retry_interval = health_config.get('connection_retry_interval', 5)
            
            print(f"PLC Data Reader initialized with {max_silence_time}s disconnect timeout")
            return config
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        sys.exit(1)


def connect_serial():
    global serial_connection, is_connected
    
    reader_config = config.get('reader', {})
    port = reader_config.get('port', 'COM2')
    baudrate = reader_config.get('baudrate', 9600)
    timeout = reader_config.get('timeout', 1)
    
    try:
        print(f"Connecting to {port}...")
        serial_connection = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )
        time.sleep(1)
        
        if serial_connection.is_open:
            print(f"Connected to {port}")
            is_connected = True
            return True
        else:
            print(f"Failed to connect to {port}")
            return False
            
    except Exception as e:
        print(f"Connection error: {e}")
        return False


def disconnect_serial():
    global serial_connection, is_connected
    
    if serial_connection and serial_connection.is_open:
        try:
            serial_connection.close()
            print("Serial connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")
    serial_connection = None
    is_connected = False


def validate_data(data: str):
    """Check expected format: TEMPERATURE:25.5,PRESSURE:101.3,SPEED:150"""
    pattern = r'^TEMPERATURE:[\d.]+,\s*PRESSURE:[\d.]+,\s*SPEED:[\d.]+$'
    return re.match(pattern, data.strip()) is not None


def parse_sensor_data(data: str):
    try:
        data = data.strip()
        
        if not validate_data(data):
            return None
        
        # Parse sensor values
        sensors = {}
        parts = data.split(',')
        
        for part in parts:
            part = part.strip()
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip().lower()
                value = float(value.strip())
                sensors[key] = value
        
        # Create sensor reading
        reading = SensorReading(
            temperature=sensors['temperature'],
            pressure=sensors['pressure'],
            speed=sensors['speed'],
            timestamp=datetime.now(),
            raw_data=data
        )
        
        return reading
        
    except Exception as e:
        print(f"Error parsing data: {e}")
        return None


def store_reading(reading):
    global last_reading, last_reading_timestamp, last_data_received, data_history
    
    # Update last reading
    last_reading = reading
    last_reading_timestamp = reading.timestamp
    last_data_received = reading.timestamp
    
    # Add to history
    data_history.append(reading)
    
    print(f"Data received: {reading.raw_data}")


def read_serial_data():
    global is_connected, is_running
    buffer = ""
    
    while not stop_event.is_set() and is_running:
        try:
            if not serial_connection or not serial_connection.is_open:
                time.sleep(1)
                continue
            
            # Read data from serial port
            if serial_connection.in_waiting > 0:
                data = serial_connection.read(serial_connection.in_waiting).decode('utf-8', errors='ignore')
                buffer += data
                
                # Process complete messages (ending with newline)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        # Parse and store the reading
                        reading = parse_sensor_data(line)
                        if reading:
                            store_reading(reading)
                        else:
                            print(f"Failed to parse data: {line}")
            
            time.sleep(0.01)
            
        except Exception as e:
            print(f"Error reading serial data: {e}")
            is_connected = False
            break


def health_check_loop():
    global is_connected, is_running
    
    while not stop_event.is_set() and is_running:
        try:
            # Check if we haven't received data for too long
            if last_data_received:
                silence_duration = (datetime.now() - last_data_received).total_seconds()
                if silence_duration > max_silence_time:
                    print(f"No data received for {silence_duration:.1f} seconds (timeout: {max_silence_time}s) - marking as disconnected")
                    is_connected = False
            elif is_connected:
                # If we think we're connected but have never received data, mark as disconnected
                print("No data ever received - marking as disconnected")
                is_connected = False
            
            # Check connection health
            if not is_connected or not check_connection_health():
                print("Connection unhealthy, attempting to reconnect...")
                disconnect_serial()
                
                if not connect_serial():
                    print("Reconnection failed")
                    time.sleep(connection_retry_interval)
                    continue
            
            time.sleep(health_check_interval)
            
        except Exception as e:
            print(f"Error in health check: {e}")
            time.sleep(health_check_interval)


def check_connection_health():
    if not serial_connection:
        return False
    
    try:
        return serial_connection.is_open
    except Exception as e:
        print(f"Connection health check failed: {e}")
        return False


def start_plc_reader():
    global is_running, stop_event
    
    print("Starting PLC Data Reader...")
    is_running = True
    stop_event.clear()
    
    # Connect to serial port
    if not connect_serial():
        print("Failed to establish serial connection. Exiting.")
        return
    
    # Start reader thread
    reader_thread = threading.Thread(target=read_serial_data, daemon=True)
    reader_thread.start()
    
    # Start health check thread
    health_check_thread = threading.Thread(target=health_check_loop, daemon=True)
    health_check_thread.start()
    
    print("PLC Data Reader started successfully")
    print("Press Ctrl+C to stop.")
    
    try:
        # Keep main thread alive
        while is_running and not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Received keyboard interrupt")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        stop_plc_reader()


def stop_plc_reader():
    global is_running
    
    print("Stopping PLC Data Reader...")
    is_running = False
    stop_event.set()
    
    # Wait for threads to finish
    for thread in threading.enumerate():
        if thread != threading.current_thread() and thread.is_alive():
            thread.join(timeout=5)
    
    disconnect_serial()
    print("PLC Data Reader stopped")


def get_last_reading():
    return last_reading


def get_last_reading_timestamp():
    return last_reading_timestamp


def get_data_history(limit=None):
    if limit:
        return list(data_history)[-limit:]
    return list(data_history)


def is_healthy():
    if not is_connected or not last_data_received:
        return False
    
    data_age_seconds = (datetime.now() - last_data_received).total_seconds()
    return data_age_seconds <= max_silence_time


def get_connection_status():
    data_age_seconds = None
    if last_data_received:
        data_age_seconds = (datetime.now() - last_data_received).total_seconds()
    
    return {
        'is_connected': is_connected,
        'is_healthy': is_healthy(),
        'last_data_received': last_data_received.isoformat() if last_data_received else None,
        'data_age_seconds': data_age_seconds,
        'max_silence_time': max_silence_time,
        'data_history_size': len(data_history)
    }


