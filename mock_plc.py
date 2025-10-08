import serial
import random
import time
import yaml
import sys
import os


def load_config(config_file: str):
    """Load configuration from YAML file"""
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


def generate_sensor_data(config):
    """Generate mock sensor data based on configuration"""
    sensors_config = config.get('plc', {}).get('sensors', {})
    sensor_data = {}
    
    for sensor_name, sensor_config in sensors_config.items():
        min_val = sensor_config.get('min_value', 0)
        max_val = sensor_config.get('max_value', 100)
        precision = sensor_config.get('precision', 1)
        
        # Generate random 
        value = random.uniform(min_val, max_val)
        
    
        if precision == 0:
            value = round(value)
        else:
            value = round(value, precision)
        
        sensor_data[sensor_name] = value
    
    return sensor_data


def format_data_message(sensor_data):
    """Format  TEMPERATURE:25.5,PRESSURE:101.3,SPEED:150\n"""
    formatted_parts = []
    
    for sensor_name, value in sensor_data.items():
        sensor_key = sensor_name.upper()
        formatted_parts.append(f"{sensor_key}:{value}")
    
    message = ",".join(formatted_parts) + "\n"
    return message


def send_sensor_data(serial_port, config):
   
    transmission_interval = config.get('plc', {}).get('transmission_interval', 2)
    
    try:
        while True:
            sensor_data = generate_sensor_data(config)
            message = format_data_message(sensor_data)
            print(f"Sending data: {message.strip()}") 

            # Send the data to the COM port
            serial_port.write(message.encode('utf-8'))
            
            # Wait
            time.sleep(transmission_interval)
            
    except KeyboardInterrupt:
        print("Received keyboard interrupt, stopping...")


def main():
    # Check if config file
    config_file = "mock_plc_config.yaml"
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found!")
        sys.exit(1)
    
    # Load configuration
    config = load_config(config_file)
    
    # Get serial port settings from config
    plc_config = config.get('plc', {})
    com_port = plc_config.get('port', 'COM1')
    baud_rate = plc_config.get('baudrate', 9600)
    timeout = plc_config.get('timeout', 1)
    
    #serial connection
    try:
        with serial.Serial(com_port, baud_rate, timeout=timeout) as ser:
            print(f"Connected to {com_port} at {baud_rate} baud.")
            send_sensor_data(ser, config)
    except serial.SerialException as e:
        print(f"Error: Could not open COM port {com_port}. {e}")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()