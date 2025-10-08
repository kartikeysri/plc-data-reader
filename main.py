import threading
import time
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from plc_reader import (
    load_config, start_plc_reader, stop_plc_reader,
    get_last_reading, get_last_reading_timestamp, get_data_history,
    get_connection_status
)


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


# Global status
plc_initialized = False


def start_plc_service():
    global plc_initialized
    
    try:
        load_config("plc_reader_config.yaml")
        reader_thread = threading.Thread(target=start_plc_reader, daemon=True)
        reader_thread.start()
        time.sleep(2)
        plc_initialized = True
        print("PLC Reader started")
    except Exception as e:
        print(f"Failed to start PLC Reader: {e}")
        plc_initialized = False


app = FastAPI(title="PLC Data Reader API", version="1.0.0")


@app.on_event("startup")
async def startup():
    start_plc_service()


@app.on_event("shutdown")
async def shutdown():
    global plc_initialized
    if plc_initialized:
        stop_plc_reader()


@app.get("/api/data", response_model=SensorData)
async def get_latest_data():
    global plc_initialized
    
    if not plc_initialized:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "PLC Reader not initialized",
                "message": "PLC Reader service is not available"
            }
        )
    
    last_reading = get_last_reading()
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
    global plc_initialized
    
    if not plc_initialized:
        raise HTTPException(status_code=503, detail="PLC Reader not initialized")
    
    last_reading = get_last_reading()
    if not last_reading:
        raise HTTPException(status_code=404, detail="No data available")
    
    sensor_mapping = {
        "temperature": {"value": last_reading.temperature, "unit": "°C"},
        "pressure": {"value": last_reading.pressure, "unit": "kPa"},
        "speed": {"value": last_reading.speed, "unit": "RPM"}
    }
    
    if sensor_name.lower() not in sensor_mapping:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_name}' not found")
    
    sensor_data = sensor_mapping[sensor_name.lower()]
    return SensorValue(
        value=sensor_data["value"],
        unit=sensor_data["unit"],
        timestamp=last_reading.timestamp.isoformat()
    )


@app.get("/api/health", response_model=HealthStatus)
async def health_check():
    global plc_initialized
    
    if not plc_initialized:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "disconnected",
                "error": "PLC Reader not initialized"
            }
        )
    
    connection_status = get_connection_status()
    last_timestamp = get_last_reading_timestamp()
    
    if connection_status["is_healthy"]:
        return HealthStatus(
            status="connected",
            last_update=last_timestamp.isoformat() if last_timestamp else None,
            data_age_seconds=connection_status.get("data_age_seconds")
        )
    else:
        error_reason = "PLC connection unhealthy"
        if not connection_status["is_connected"]:
            error_reason = "Serial port not connected"
        elif connection_status.get("data_age_seconds") is not None:
            data_age = connection_status["data_age_seconds"]
            max_silence = connection_status.get("max_silence_time", 10)
            error_reason = f"No data received for {data_age:.1f} seconds (timeout: {max_silence}s)"
        
        raise HTTPException(
            status_code=503,
            detail={
                "status": "disconnected",
                "error": error_reason
            }
        )


@app.get("/api/history", response_model=DataHistory)
async def get_data_history_endpoint():
    global plc_initialized
    
    if not plc_initialized:
        raise HTTPException(status_code=503, detail="PLC Reader not initialized")
    
    history = get_data_history()
    if not history:
        raise HTTPException(status_code=404, detail="No data history available")
    
    readings = [
        SensorData(
            temp=reading.temperature,
            pressure=reading.pressure,
            speed=reading.speed,
            timestamp=reading.timestamp.isoformat()
        ) for reading in history
    ]
    
    return DataHistory(readings=readings, total_count=len(readings))


@app.get("/")
async def root():
    return {"message": "PLC Data Reader API", "version": "1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)