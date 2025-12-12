#!/bin/bash

# Script để stop Spark Cluster trên Spark Machine

echo "Stopping Spark Cluster..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

chmod +x stop_spark_cluster.sh
./stop_spark_cluster.sh

echo "Spark Cluster Stopped"

