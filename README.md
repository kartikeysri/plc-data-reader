### Overview:
The project is PLC (programmable logic Controller) data monitoring system in which we simulate the mock PLC using virtual port and it gives live sensor reading through the Rest api.
  •	PLC mock simulator – It creates a random sensor value for the port.
  •	PLC reader – It is used to read the value which are generated through mock plc.
  •	Api – Api is used a bridge to get that data to use on web dashboard.
The user is can view:
  •	Latest sensor reading
  •	Health of Sensor
  •	Record of reading (In this case only 100 entries)
  •	Specific sensor value

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Configure the System

**Edit `mock_plc_config.yaml`:**
```yaml
plc:
  port: "COM1"  # Change this to your PLC port
  transmission_interval: 2  # Send data every 2 seconds
```

**Edit `plc_reader_config.yaml`:**
```yaml
reader:
  port: "COM2"  # Change this to your reader port
  baudrate: 9600
```

### Run the System

**Terminal 1 - Start the Mock PLC:**
```bash
python mock_plc.py
```

**Terminal 2 - Start the API Server:**
```bash
python main.py
```

**Terminal 3 - Test the API:**
```bash
./test_api.sh
```

## API Endpoints

- `GET /api/data` - Get latest sensor data
- `GET /api/data/temp` - Get temperature only
- `GET /api/data/pressure` - Get pressure only  
- `GET /api/data/speed` - Get speed only
- `GET /api/health` - Check if system is working
- `GET /api/history` - Get last 100 readings


### Known Issues/Limitations	
•The Limit on storing the data when the large set of data will be there it will generate  the error.
•The data is store is temporary as the program is closed all data will be reset.
•For the huge data Database is required.

###  What I Learned:
- About com0com.
- How to setup and install com0com.
- Python different libraries.
- Threading in Python
- Using YAML file for Config 
- Fast Api
- How to set connection between port and script.
- About PLC and serial Connection.

