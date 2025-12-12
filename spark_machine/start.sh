#!/bin/bash

# Script để start Spark Cluster trên Spark Machine
# Chạy script này trên Spark machine sau khi clone từ GitHub

echo "=========================================="
echo "Starting Spark Cluster"
echo "=========================================="

# Check SPARK_HOME
if [ -z "$SPARK_HOME" ]; then
    if [ -d "/opt/spark" ]; then
        export SPARK_HOME=/opt/spark
    else
        echo "Error: SPARK_HOME is not set and /opt/spark does not exist"
        echo "Please set SPARK_HOME environment variable or install Spark to /opt/spark"
        exit 1
    fi
fi

echo "SPARK_HOME: $SPARK_HOME"

# Get machine IP
MACHINE_IP=$(hostname -I | awk '{print $1}')
SPARK_MASTER_PORT=7077

echo "Machine IP: $MACHINE_IP"
echo "Master URL: spark://$MACHINE_IP:$SPARK_MASTER_PORT"

# Update IP in scripts
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

sed -i "s/spark-machine-ip/$MACHINE_IP/g" start_spark_cluster.sh
sed -i "s/spark-machine-ip/$MACHINE_IP/g" verify_spark_cluster.sh

# Update configs
if [ -f "configs/spark-defaults.conf" ]; then
    # Create backup
    cp configs/spark-defaults.conf configs/spark-defaults.conf.bak
    sed -i "s/spark-machine-ip/$MACHINE_IP/g" configs/spark-defaults.conf
    
    # Get Kafka IP (ask user or use placeholder)
    read -p "Enter Kafka Machine IP (or press Enter to keep placeholder): " KAFKA_IP
    if [ -n "$KAFKA_IP" ]; then
        sed -i "s/kafka-machine-ip/$KAFKA_IP/g" configs/spark-defaults.conf
    fi
    
    # Copy to SPARK_HOME if not exists or update
    echo "Updating spark-defaults.conf in $SPARK_HOME/conf/"
    sudo cp configs/spark-defaults.conf $SPARK_HOME/conf/
fi

# Create directories
echo "Creating directories..."
sudo mkdir -p /models /checkpoints
sudo chmod 777 /models /checkpoints

# Start Spark
echo "Starting Spark Master and Workers..."
chmod +x start_spark_cluster.sh
./start_spark_cluster.sh

# Wait a bit
sleep 10

# Verify
echo "Verifying Spark Cluster..."
chmod +x verify_spark_cluster.sh
./verify_spark_cluster.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Spark Cluster Started Successfully!"
    echo "=========================================="
    echo "Master URL: spark://$MACHINE_IP:$SPARK_MASTER_PORT"
    echo "Web UI: http://$MACHINE_IP:8080"
    echo ""
    echo "To stop Spark, run: ./stop.sh"
else
    echo "✗ Spark Cluster verification failed"
    exit 1
fi

