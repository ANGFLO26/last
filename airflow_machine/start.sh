#!/bin/bash

# Script để start Airflow trên Airflow Machine
# Chạy script này trên Airflow machine sau khi clone từ GitHub

echo "=========================================="
echo "Starting Airflow Services"
echo "=========================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Set AIRFLOW_HOME
export AIRFLOW_HOME="$SCRIPT_DIR"
echo "AIRFLOW_HOME: $AIRFLOW_HOME"

# Check if Airflow is installed
if ! command -v airflow &> /dev/null; then
    echo "Error: Airflow is not installed"
    echo "Please install: pip install -r requirements.txt"
    exit 1
fi

# Check if database is initialized
if [ ! -d "$AIRFLOW_HOME/airflow.db" ] && [ ! -f "$AIRFLOW_HOME/airflow.cfg" ]; then
    echo "Initializing Airflow database..."
    airflow db init
    
    echo "Creating admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin
fi

# Update IPs in DAG
echo "Updating IPs in DAG..."
MACHINE_IP=$(hostname -I | awk '{print $1}')

# Get Kafka and Spark IPs from user or use defaults
read -p "Enter Kafka Machine IP (or press Enter to use placeholder): " KAFKA_IP
read -p "Enter Spark Machine IP (or press Enter to use placeholder): " SPARK_IP

if [ -n "$KAFKA_IP" ]; then
    sed -i "s/kafka-machine-ip/$KAFKA_IP/g" dags/fraud_detection_pipeline.py
fi

if [ -n "$SPARK_IP" ]; then
    sed -i "s/spark-machine-ip/$SPARK_IP/g" dags/fraud_detection_pipeline.py
fi

# Update IPs in scripts
if [ -n "$KAFKA_IP" ]; then
    find scripts/ -name "*.py" -type f -exec sed -i "s/kafka-machine-ip/$KAFKA_IP/g" {} \;
    find utils/ -name "*.py" -type f -exec sed -i "s/kafka-machine-ip/$KAFKA_IP/g" {} \;
fi

if [ -n "$SPARK_IP" ]; then
    find scripts/ -name "*.py" -type f -exec sed -i "s/spark-machine-ip/$SPARK_IP/g" {} \;
    find utils/ -name "*.py" -type f -exec sed -i "s/spark-machine-ip/$SPARK_IP/g" {} \;
fi

# Create logs directory if not exists
mkdir -p logs

# Start Airflow Scheduler (background)
echo "Starting Airflow Scheduler..."
airflow scheduler > logs/scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo "Scheduler PID: $SCHEDULER_PID"
echo $SCHEDULER_PID > .scheduler.pid

# Start Airflow Webserver
echo "Starting Airflow Webserver..."
echo "Airflow UI will be available at: http://$MACHINE_IP:8080"
echo "Default credentials: admin/admin"
echo ""
echo "Press Ctrl+C to stop Airflow"
echo ""

airflow webserver -p 8080

