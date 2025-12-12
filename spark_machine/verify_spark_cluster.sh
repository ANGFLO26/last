#!/bin/bash

# Script để verify Spark cluster đã sẵn sàng
# Dùng cho Airflow task verify_spark_cluster

SPARK_MASTER_IP=${SPARK_MASTER_IP:-spark-machine-ip}
SPARK_MASTER_PORT=${SPARK_MASTER_PORT:-7077}
SPARK_WEB_UI_PORT=${SPARK_WEB_UI_PORT:-8080}

echo "Verifying Spark Cluster..."
echo "Master URL: spark://$SPARK_MASTER_IP:$SPARK_MASTER_PORT"
echo "Web UI: http://$SPARK_MASTER_IP:$SPARK_WEB_UI_PORT"

# Check Spark Master port
if nc -z $SPARK_MASTER_IP $SPARK_MASTER_PORT 2>/dev/null; then
    echo "✓ Spark Master port $SPARK_MASTER_PORT is accessible"
else
    echo "✗ Spark Master port $SPARK_MASTER_PORT is NOT accessible"
    exit 1
fi

# Check Spark Web UI
if curl -s http://$SPARK_MASTER_IP:$SPARK_WEB_UI_PORT > /dev/null; then
    echo "✓ Spark Web UI is accessible"
else
    echo "✗ Spark Web UI is NOT accessible"
    exit 1
fi

# Check Spark connection
if command -v spark-submit &> /dev/null; then
    echo "Testing Spark connection..."
    spark-submit --master spark://$SPARK_MASTER_IP:$SPARK_MASTER_PORT --version > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Spark connection test successful"
    else
        echo "✗ Spark connection test failed"
        exit 1
    fi
else
    echo "⚠ spark-submit not found, skipping connection test"
fi

echo ""
echo "Spark Cluster is ready!"
exit 0

