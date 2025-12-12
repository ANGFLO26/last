#!/bin/bash

# Script để start Spark Master và Workers
# Chạy trên Spark machine

SPARK_HOME=${SPARK_HOME:-/opt/spark}
SPARK_MASTER_IP=${SPARK_MASTER_IP:-spark-machine-ip}
SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}

echo "Starting Spark Cluster..."
echo "SPARK_HOME: $SPARK_HOME"
echo "Master URL: spark://$SPARK_MASTER_IP:$SPARK_MASTER_PORT"

# Start Spark Master
echo "Starting Spark Master..."
$SPARK_HOME/sbin/start-master.sh

# Wait a bit for master to start
sleep 5

# Start Spark Worker
echo "Starting Spark Worker..."
$SPARK_HOME/sbin/start-worker.sh spark://$SPARK_MASTER_IP:$SPARK_MASTER_PORT

echo "Spark Cluster started!"
echo "Master Web UI: http://$SPARK_MASTER_IP:8080"
echo "Master URL: spark://$SPARK_MASTER_IP:$SPARK_MASTER_PORT"

