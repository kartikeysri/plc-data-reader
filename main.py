import threading
import time
from datetime import datetime
from typing import List
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from plc_reader import PLCDataReader


# API response models
class SensorData(BaseModel):
    temp: float
    pressure: float
    speed: float
    timestamp: str


class SensorValue(BaseModel):
    value: float
    unit: str
    timestamp: str


class HealthStatus(BaseModel):
    status: str
    last_update: str = None
    data_age_seconds: float = None


class DataHistory(BaseModel):
    readings: List[SensorData]
    total_count: int

plc_reader = None
reader_thread = None


def start_plc_reader():
    global plc_reader, reader_thread
    
    try:
        plc_reader = PLCDataReader("plc_reader_config.yaml")
        
        
        reader_thread = threading.Thread(target=plc_reader.start, daemon=True)
        reader_thread.start()
        
    
        time.sleep(2)
        
        print("PLC Reader started successfully")
        
    except Exception as e:
        print(f"Failed to start PLC Reader: {e}")
        plc_reader = None



app = FastAPI(
    title="PLC Data Reader API",
    description="REST API for reading sensor data from PLC via serial communication",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    print("Starting PLC Data Reader API...")
    start_plc_reader()


@app.on_event("shutdown")
async def shutdown_event():
    global plc_reader
    if plc_reader:
        print("Stopping PLC Reader...")
        plc_reader.stop()


@app.get("/api/data", response_model=SensorData)
async def get_latest_data():
    global plc_reader
    
    if not plc_reader:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "PLC Reader not initialized",
                "message": "PLC Reader service is not available"
            }
        )
    
 
    last_reading = plc_reader.get_last_reading()
    
    if not last_reading:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "No data available",
                "message": "Waiting for PLC data..."
            }
        )
    
    
    return SensorData(
        temp=last_reading.temperature,
        pressure=last_reading.pressure,
        speed=last_reading.speed,
        timestamp=last_reading.timestamp.isoformat()
    )


@app.get("/api/data/{sensor_name}", response_model=SensorValue)
async def get_specific_sensor(sensor_name: str):
    global plc_reader
    
    if not plc_reader:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "PLC Reader not initialized",
                "message": "PLC Reader service is not available"
            }
        )
    
   
    last_reading = plc_reader.get_last_reading()
    
    if not last_reading:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Sensor not found",
                "message": "No data available for any sensor"
            }
        )
    
    
    sensor_mapping = {
        "temperature": {
            "value": last_reading.temperature,
            "unit": "°C"
        },
        "pressure": {
            "value": last_reading.pressure,
            "unit": "kPa"
        },
        "speed": {
            "value": last_reading.speed,
            "unit": "RPM"
        }
    }
    
    
    if sensor_name.lower() not in sensor_mapping:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Sensor not found",
                "message": f"Sensor '{sensor_name}' is not available. Available sensors: temp, pressure, speed"
            }
        )
    
    sensor_data = sensor_mapping[sensor_name.lower()]
    
    return SensorValue(
        value=sensor_data["value"],
        unit=sensor_data["unit"],
        timestamp=last_reading.timestamp.isoformat()
    )


@app.get("/api/health", response_model=HealthStatus)
async def health_check():
    global plc_reader
    
    if not plc_reader:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "disconnected",
                "error": "PLC Reader not initialized"
            }
        )
    
  
    connection_status = plc_reader.get_connection_status()
    last_reading = plc_reader.get_last_reading()
    last_timestamp = plc_reader.get_last_reading_timestamp()
    
    
    if connection_status["is_healthy"]:
        status = "connected"
        last_update = last_timestamp.isoformat() if last_timestamp else None
        data_age_seconds = connection_status.get("data_age_seconds")
        
        return HealthStatus(
            status=status,
            last_update=last_update,
            data_age_seconds=data_age_seconds
        )
    else:
       
        error_reason = "PLC connection unhealthy"
        if not connection_status["is_connected"]:
            error_reason = "Serial port not connected"
        elif connection_status.get("data_age_seconds") is not None:
            data_age = connection_status["data_age_seconds"]
            max_silence = connection_status.get("max_silence_time", 10)
            error_reason = f"No data received for {data_age:.1f} seconds (timeout: {max_silence}s)"
        elif not last_reading:
            error_reason = "No data received"
        
        raise HTTPException(
            status_code=503,
            detail={
                "status": "disconnected",
                "error": error_reason,
                "data_age_seconds": connection_status.get("data_age_seconds"),
                "max_silence_time": connection_status.get("max_silence_time")
            }
        )

@app.get("/api/history", response_model=DataHistory)
async def get_data_history():
    global plc_reader
     
    if not plc_reader:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "PLC Reader not initialized",
                "message": "PLC Reader service is not available"
            }
        )
    

    history = plc_reader.get_data_history()
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No data history available",
                "message": "No historical data has been collected yet"
            }
        )
    
    
    readings = []
    for reading in history:
        readings.append(SensorData(
            temp=reading.temperature,
            pressure=reading.pressure,
            speed=reading.speed,
            timestamp=reading.timestamp.isoformat()
        ))
    
    return DataHistory(
        readings=readings,
        total_count=len(readings)
    )


@app.get("/")
async def root():
    return {
        "message": "PLC Data Reader API",
        "version": "1.0.0",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
