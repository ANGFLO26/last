#!/bin/bash

# Script để stop Spark Master và Workers

SPARK_HOME=${SPARK_HOME:-/opt/spark}

echo "Stopping Spark Cluster..."

# Stop Worker
echo "Stopping Spark Worker..."
$SPARK_HOME/sbin/stop-worker.sh

# Stop Master
echo "Stopping Spark Master..."
$SPARK_HOME/sbin/stop-master.sh

echo "Spark Cluster stopped!"

