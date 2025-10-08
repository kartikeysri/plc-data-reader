# Assignment: PLC Data Reader

## Overview

Build a simple system that reads sensor data from a simulated PLC (via serial port) and exposes it through REST API.

**Timeline:** 5 days

**What you'll need to know/learn:**

- Serial communication basics
- How to simulate hardware without having actual hardware
- Building REST APIs in Python
- Reading technical documentation

## Background

PLCs (Programmable Logic Controllers) are industrial computers that control machinery. They often send data to other systems via serial communication. In this assignment, you'll simulate a PLC that sends sensor readings, and build a program that reads and exposes this data via REST API.

## Part 1: Setup Virtual Serial Ports

You need two serial ports that talk to each other (one acts as PLC, other as your reader). If you are on Linux/Mac, you may want to explore `socat` and on Windows, you can check [com0com](https://sourceforge.net/projects/com0com/)

## Part 2: Create Mock PLC

Create `mock_plc.py` that simulates a PLC sending sensor data:

**Requirements:**

- Sends data every 2 seconds
- Data format: `TEMP:25.5,PRESSURE:101.3,SPEED:150\n`
- Use random values within ranges:
  - Temperature: 20-30°C
  - Pressure: 95-105 kPa
  - Speed: 100-200 RPM

## Part 3: Build Data Reader with REST API

### 3.1 Required API Endpoints

**1. Get Latest Data**

```
GET /api/data

Response (200 OK):
{
    "temp": 25.5,
    "pressure": 101.3,
    "speed": 150,
    "timestamp": "2025-01-06T10:30:22"
}

Response (503 Service Unavailable) if no data received yet:
{
    "error": "No data available",
    "message": "Waiting for PLC data..."
}
```

**2. Get Specific Sensor**

```
GET /api/data/temp
GET /api/data/pressure
GET /api/data/speed

Response (200 OK):
{
    "value": 25.5,
    "unit": "°C",
    "timestamp": "2025-01-06T10:30:22"
}

Response (404 Not Found) if sensor not available:
{
    "error": "Sensor not found"
}
```

**3. Health Check**

```
GET /api/health

Response (200 OK):
{
    "status": "connected",
    "last_update": "2025-01-06T10:30:22",
    "data_age_seconds": 1.5
}

Response (503 Service Unavailable) if not connected:
{
    "status": "disconnected",
    "error": "Serial port not connected"
}
```

## Part 4: Testing & Documentation

### 4.1 Manual Testing

Create `test_api.sh` with curl commands:

```bash
#!/bin/bash

echo "Testing PLC Data Reader API"
echo "============================"

echo -e "\n1. Health Check:"
curl http://localhost:8000/api/health

echo -e "\n\n2. Get Latest Data:"
curl http://localhost:8000/api/data

echo -e "\n\n3. Get Temperature:"
curl http://localhost:8000/api/data/temp
```

### 4.2 README.md

Write a README with:

1. **Project Overview** (2-3 sentences about what it does)
2. **Setup Instructions:**
   - How to set up virtual serial ports
   - How to install dependencies
   - How to run mock PLC
   - How to run the API
3. **API Documentation:**
   - List all endpoints
   - Show example request/response for each
4. **Testing:**
   - How to test if it works
5. **Known Issues/Limitations**
6. **What I Learned** (brief section about challenges faced)

## Deliverables

Submit a GitHub repository with:

```
plc-data-reader/
├── mock_plc.py          # Your PLC simulator
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── test_api.sh          # Testing script
├── README.md            # Documentation
└── .gitignore          # Git ignore file
```

## How to Demo your Running System

**Terminal 1**: Virtual Serial Ports

**Terminal 2**: Mock PLC

**Terminal 3:** Your API

**Terminal 4:** Test

## Evaluation Criteria

**Basic Functionality**

- Mock PLC sends data correctly
- API can read from serial port
- All 4 endpoints work

**Code Quality**

- Clean, readable code
- Proper error handling

**Documentation**

- Clear README with all sections
- Code comments where needed

**Problem Solving**

- Shows understanding of serial communication
- Handles edge cases

## Tips

1. **Start with mock_plc.py** - Get it working first
2. **Test serial reading separately** - Before adding FastAPI
3. **Add endpoints one at a time** - Don't try to do everything at once
4. **Use print() statements** - To debug what data you're receiving
5. **Handle errors gracefully** - What if PLC disconnects?

## Bonus (Optional - Extra Credit)

If you finish early, add these features:

1. **Data History** - Store last 100 readings, add endpoint to retrieve them
2. **Configuration File** - Use JSON/YAML for port settings
3. **Web UI** - Simple HTML page that shows live data (auto-refresh)

## Questions?

If anything is unclear, feel free to ask. The goal is to see:

- Can you figure out serial communication?
- Can you build working REST API?
- Can you write clear documentation?
- How do you handle problems?

Feel free to take help from AI/LLM but it's expected that you thorougly understand what you've delivered and can explain when asked.

Good luck!