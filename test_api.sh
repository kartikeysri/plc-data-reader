#!/bin/bash

echo "Testing PLC Data Reader API"

echo -e "\n1. Health Check:"
curl -s http://localhost:8000/api/health 

echo -e "\n\n2. Get Latest Data:"
curl -s http://localhost:8000/api/data 

echo -e "\n\n3. Get Temperature:"
curl -s http://localhost:8000/api/data/temperature

echo -e "\n\n4. Get Pressure:"
curl -s http://localhost:8000/api/data/pressure 

echo -e "\n\n5. Get Speed:"
curl -s http://localhost:8000/api/data/speed 

echo -e "\n\n6. Get Data History:"
curl -s http://localhost:8000/api/history 

echo -e "\n\n7. Test Invalid Sensor:"
curl -s http://localhost:8000/api/data/invalid 

echo -e "\n\nAPI Testing Complete!"

