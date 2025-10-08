import serial
import time
import yaml
import sys
import threading
import re
from datetime import datetime
from typing import Optional, List
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


class PLCDataReader:
    def __init__(self, config_file: str = "plc_reader_config.yaml"):
        self.config = self._load_config(config_file)
        self.serial_connection = None
        self.is_running = False
        
        # Data storage
        self.last_reading = None
        self.last_reading_timestamp = None
        self.data_history = deque(maxlen=100)
        
        # status
        self.is_connected = False
        self.last_data_received = None
        
        # Health
        health_config = self.config.get('reader', {}).get('health', {})
        self.max_silence_time = health_config.get('max_silence_time', 10)  
        self.health_check_interval = health_config.get('check_interval', 5) 
        self.connection_retry_interval = health_config.get('connection_retry_interval', 5)
        
        
        self.reader_thread = None
        self.health_check_thread = None
        self._stop_event = threading.Event()
        
    
    def _load_config(self, config_file: str):
        try:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
                print(f"Configuration loaded from {config_file}")
                return config
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration: {e}")
            sys.exit(1)
    
    def _connect_serial(self):
        reader_config = self.config.get('reader', {})
        port = reader_config.get('port', 'COM2')
        baudrate = reader_config.get('baudrate', 9600)
        timeout = reader_config.get('timeout', 1)
        
        try:
            print(f"Connecting to {port}...")
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            time.sleep(1)
            
            if self.serial_connection.is_open:
                print(f"Connected to {port}")
                self.is_connected = True
                return True
            else:
                print(f"Failed to connect to {port}")
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def _disconnect_serial(self):
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                print("Serial connection closed")
            except Exception as e:
                print(f"Error closing connection: {e}")
        self.serial_connection = None
        self.is_connected = False
    
    def _validate_data(self, data: str):
        # Examaple TEMPERATURE:25.5,PRESSURE:101.3,SPEED:150
        pattern = r'^TEMPERATURE:[\d.]+,\s*PRESSURE:[\d.]+,\s*SPEED:[\d.]+$'
        return re.match(pattern, data.strip()) is not None
    
    def _parse_sensor_data(self, data: str):
        try:
            data = data.strip()
            
            if not self._validate_data(data):
                return None
            
        
            sensors = {}
            parts = data.split(',')
            
            for part in parts:
                part = part.strip()
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = float(value.strip())
                    sensors[key] = value
            

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
    
    def _store_reading(self, reading):
        self.last_reading = reading
        self.last_reading_timestamp = reading.timestamp
        self.last_data_received = reading.timestamp
        
        self.data_history.append(reading)
        
        print(f"Data received: {reading.raw_data}")
    
    def _read_serial_data(self):
        buffer = ""
        
        while not self._stop_event.is_set() and self.is_running:
            try:
                if not self.serial_connection or not self.serial_connection.is_open:
                    time.sleep(1)
                    continue
                
               
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
            
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                          
                            reading = self._parse_sensor_data(line)
                            if reading:
                                self._store_reading(reading)
                            else:
                                print(f"Failed to parse data: {line}")
                
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error reading serial data: {e}")
                self.is_connected = False
                break
    
    def _health_check_loop(self):
        while not self._stop_event.is_set() and self.is_running:
            try:
            
                if self.last_data_received:
                    silence_duration = (datetime.now() - self.last_data_received).total_seconds()
                    if silence_duration > self.max_silence_time:
                        print(f"No data received for {silence_duration:.1f} seconds (timeout: {self.max_silence_time}s) - marking as disconnected")
                        self.is_connected = False
                elif self.is_connected:
                    print("No data ever received - marking as disconnected")
                    self.is_connected = False
                
                if not self.is_connected or not self._check_connection_health():
                    print("Connection unhealthy, attempting to reconnect...")
                    self._disconnect_serial()
                    
                    if not self._connect_serial():
                        print("Reconnection failed")
                        time.sleep(self.connection_retry_interval)
                        continue
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                print(f"Error in health check: {e}")
                time.sleep(self.health_check_interval)
    
    def _check_connection_health(self):
        if not self.serial_connection:
            return False
        
        try:
            return self.serial_connection.is_open
        except Exception as e:
            print(f"Connection health check failed: {e}")
            return False
    
    def start(self):
        print("Starting PLC Data Reader...")
        self.is_running = True
        self._stop_event.clear()
        
       
        if not self._connect_serial():
            print("Failed to establish serial connection. Exiting.")
            return
        
        
        self.reader_thread = threading.Thread(target=self._read_serial_data, daemon=True)
        self.reader_thread.start()
        
        
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
        
        print("PLC started")
        
        try:
            while self.is_running and not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            print("Received keyboard interrupt")
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        print("Stopping PLC Data Reader...")
        self.is_running = False
        self._stop_event.set()
        
        
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=5)
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        
        self._disconnect_serial()
        print("PLC Data Reader stopped")
    
    def get_last_reading(self):
        return self.last_reading
    
    def get_last_reading_timestamp(self):
        return self.last_reading_timestamp
    
    def get_data_history(self, limit=None):
        if limit:
            return list(self.data_history)[-limit:]
        return list(self.data_history)
    
    def is_healthy(self):
        if not self.is_connected or not self.last_data_received:
            return False
        
        data_age_seconds = (datetime.now() - self.last_data_received).total_seconds()
        return data_age_seconds <= self.max_silence_time
    
    def get_connection_status(self):
        data_age_seconds = None
        if self.last_data_received:
            data_age_seconds = (datetime.now() - self.last_data_received).total_seconds()
        
        return {
            'is_connected': self.is_connected,
            'is_healthy': self.is_healthy(),
            'last_data_received': self.last_data_received.isoformat() if self.last_data_received else None,
            'data_age_seconds': data_age_seconds,
            'max_silence_time': self.max_silence_time,
            'data_history_size': len(self.data_history)
        }


