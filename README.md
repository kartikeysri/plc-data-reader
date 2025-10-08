### Overview:
The project is PLC (programmable logic Controller) data monitoring system in which we simulate the mock PLC using virtual port and it gives live sensor reading through the Rest api.
  -	PLC mock simulator – It creates a random sensor value for the port.
  -	PLC reader – It is used to read the value which are generated through mock plc.
  -	Api – Api is used a bridge to get that data to use on web dashboard.

The user is can view:
  -	Latest sensor reading
  -	Health of Sensor
  -	Record of reading (In this case only 100 entries)
  -	Specific sensor value

### Install Virtual Serial Ports

**For Windows:**
1. Download and install [com0com](https://sourceforge.net/projects/com0com/)
2. Run the installer as administrator
3. Open "Setup Command Prompt" from the start menu
4. Type: `install PortName=COM1 PortName=COM2`
5. This creates two virtual ports that talk to each other

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
## API Examples

### 1. Get Latest Data
**URL:** `GET /api/data`

**Example Request:**
```bash
curl http://localhost:8000/api/data
```

**Example Response:**
```json
{
  "temp": 25.5,
  "pressure": 101.3,
  "speed": 150,
  "timestamp": "2025-01-06T10:30:22"
}
```

**Error Response (no data):**
```json
{
  "error": "No data available",
  "message": "Waiting for PLC data..."
}
```

---

### 2. Get Specific Sensor - Temperature
**URL:** `GET /api/data/temperature`

**Example Request:**
```bash
curl http://localhost:8000/api/data/temperature
```

**Example Response:**
```json
{
  "value": 25.5,
  "unit": "°C",
  "timestamp": "2025-01-06T10:30:22"
}
```

---

### 3. Get Specific Sensor - Pressure
**URL:** `GET /api/data/pressure`

**Example Request:**
```bash
curl http://localhost:8000/api/data/pressure
```

**Example Response:**
```json
{
  "value": 101.3,
  "unit": "kPa",
  "timestamp": "2025-01-06T10:30:22"
}
```

---

### 4. Get Specific Sensor - Speed
**URL:** `GET /api/data/speed`

**Example Request:**
```bash
curl http://localhost:8000/api/data/speed
```

**Example Response:**
```json
{
  "value": 150,
  "unit": "RPM",
  "timestamp": "2025-01-06T10:30:22"
}
```

**Error Response (invalid sensor):**
```json
{
  "error": "Sensor not found",
  "message": "Sensor 'invalid' is not available. Available sensors: temp, pressure, speed"
}
```

---

### 5. Health Check
**URL:** `GET /api/health`

**Example Request:**
```bash
curl http://localhost:8000/api/health
```

**Example Response (healthy):**
```json
{
  "status": "connected",
  "last_update": "2025-01-06T10:30:22",
  "data_age_seconds": 1.5
}
```

**Error Response (unhealthy):**
```json
{
  "status": "disconnected",
  "error": "Serial port not connected or no data received"
}
```

---

### 6. Data History
**URL:** `GET /api/history`

**Example Request:**
```bash
curl http://localhost:8000/api/history
```

**Example Response:**
```json
{
  "readings": [
    {
      "temp": 25.5,
      "pressure": 101.3,
      "speed": 150,
      "timestamp": "2025-01-06T10:30:22"
    },
    {
      "temp": 26.1,
      "pressure": 102.1,
      "speed": 155,
      "timestamp": "2025-01-06T10:30:24"
    },
    {
      "temp": 24.8,
      "pressure": 100.5,
      "speed": 148,
      "timestamp": "2025-01-06T10:30:26"
    }
  ],
  "total_count": 3
}
```



### Known Issues/Limitations	
- The Limit on storing the data when the large set of data will be there it will generate  the error.
- The data is store is temporary as the program is closed all data will be reset.
- For the huge data Database is required.

###  What I Learned:
- About com0com.
- How to setup and install com0com.
- Python different libraries.
- Threading in Python.
- Using YAML file for Config.
- Fast Api.
- How to set connection between port and script.
- About PLC and serial Connection.
- Learn about MD(Markup language).
