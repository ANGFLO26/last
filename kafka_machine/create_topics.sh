#!/bin/bash

# Script để tạo Kafka topics
# Chạy sau khi Kafka đã start (trong Docker container)

KAFKA_BOOTSTRAP="localhost:9092"

echo "Creating Kafka topics..."

# Check if running inside container or need to exec into container
if [ -f "/usr/bin/kafka-topics.sh" ] || command -v kafka-topics.sh &> /dev/null; then
    # Running inside container or kafka-tools installed locally
    KAFKA_CMD="kafka-topics.sh"
else
    # Need to run inside Docker container
    KAFKA_CMD="docker exec kafka kafka-topics.sh"
    KAFKA_BOOTSTRAP="localhost:29092"  # Internal port
fi

# Topic 1: input_stream - Nhận dữ liệu từ Producer
$KAFKA_CMD --create \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --topic input_stream \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --if-not-exists

# Topic 2: prediction_output - Nhận kết quả từ Spark Streaming
$KAFKA_CMD --create \
  --bootstrap-server $KAFKA_BOOTSTRAP \
  --topic prediction_output \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --if-not-exists

echo "Topics created successfully!"
echo ""
echo "Listing topics:"
$KAFKA_CMD --list --bootstrap-server $KAFKA_BOOTSTRAP

