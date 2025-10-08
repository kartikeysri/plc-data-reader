import serial
import time
import random
import yaml
import sys
import signal
import os


class MockPLC:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = self._load_config(config_file)
        self.serial_connection = None
        self.is_running = False
        self.retry_count = 0
        
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("Mock PLC initialized")
    
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
    
    def _signal_handler(self, signum, frame):
        print(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _connect_serial(self):
        plc_config = self.config.get('plc', {})
        port = plc_config.get('port', 'COM1')
        baudrate = plc_config.get('baudrate', 9600)
        timeout = plc_config.get('timeout', 1)
        
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
                self.retry_count = 0
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
    
    def _generate_sensor_data(self):
        sensors_config = self.config.get('plc', {}).get('sensors', {})
        sensor_data = {}
        
        for sensor_name, sensor_config in sensors_config.items():
            min_val = sensor_config.get('min_value', 0)
            max_val = sensor_config.get('max_value', 100)
            precision = sensor_config.get('precision', 1)
            
            # Generate random value within range
            value = random.uniform(min_val, max_val)
            
            if precision == 0:
                value = round(value)
            else:
                value = round(value, precision)
            
            sensor_data[sensor_name] = value
        
        return sensor_data
    
    def _format_data_message(self, sensor_data):
        # Format: TEMPERATURE:25.5,PRESSURE:101.3,SPEED:150\n
        formatted_parts = []
        
        for sensor_name, value in sensor_data.items():
            sensor_key = sensor_name.upper()
            formatted_parts.append(f"{sensor_key}:{value}")
        
        message = ",".join(formatted_parts) + "\n"
        return message
    
    def _send_data(self, data: str):
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Serial connection not available")
            return False
        
        try:
            # Convert string to bytes and send
            data_bytes = data.encode('utf-8')
            bytes_written = self.serial_connection.write(data_bytes)
            
            if bytes_written == len(data_bytes):
                return True
            else:
                print(f"Only sent {bytes_written} of {len(data_bytes)} bytes")
                return False
                
        except Exception as e:
            print(f"Error sending data: {e}")
            return False
    
    def _check_connection_health(self):
        if not self.serial_connection:
            return False
        
        try:
            return self.serial_connection.is_open
        except Exception as e:
            print(f"Connection health check failed: {e}")
            return False
    
    def start(self):
        print("Starting Mock PLC...")
        self.is_running = True
        
        # Connect to serial port
        if not self._connect_serial():
            print("Failed to establish serial connection. Exiting.")
            return
        
        transmission_interval = self.config.get('plc', {}).get('transmission_interval', 2)
        
        print(f"Mock PLC started. Sending data every {transmission_interval} seconds.")
        print("Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                if not self._check_connection_health():
                    print("Connection lost, attempting to reconnect...")
                    self._disconnect_serial()
                    
                    if not self._connect_serial():
                        print("Reconnection failed. Stopping PLC.")
                        break
                
                # Generate and send sensor data
                sensor_data = self._generate_sensor_data()
                message = self._format_data_message(sensor_data)
                
                if self._send_data(message):
                    print(f"Data sent: {message.strip()}")
                else:
                    print("Failed to send data")
                    self.retry_count += 1
                    
                    # If too many failures, try to reconnect
                    if self.retry_count >= 3:
                        print("Too many send failures, reconnecting...")
                        self._disconnect_serial()
                        if not self._connect_serial():
                            print("Reconnection failed. Stopping PLC.")
                            break
                        self.retry_count = 0
                
                # Wait for next transmission
                time.sleep(transmission_interval)
                
        except KeyboardInterrupt:
            print("Received keyboard interrupt")
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        print("Stopping Mock PLC...")
        self.is_running = False
        self._disconnect_serial()
        print("Mock PLC stopped")


def main():
    print("Mock PLC Simulator")
    
    # Check if config file exists
    config_file = "mock_plc_config.yaml"
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found!")
        print("Please create a config.yaml file with settings.")
        sys.exit(1)
    
    try:
        plc = MockPLC(config_file)
        plc.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
