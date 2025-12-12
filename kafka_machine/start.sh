#!/bin/bash

# Script để start Kafka trên Kafka Machine
# Chạy script này trên Kafka machine sau khi clone từ GitHub

echo "=========================================="
echo "Starting Kafka Services"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found"
    exit 1
fi

# Get machine IP (first non-localhost IP)
MACHINE_IP=$(hostname -I | awk '{print $1}')

echo "Machine IP: $MACHINE_IP"
echo "Updating docker-compose.yml with machine IP..."

# Update IP in docker-compose.yml
sed -i "s/kafka-machine-ip/$MACHINE_IP/g" docker-compose.yml

# Start Kafka
echo "Starting Kafka with Docker Compose..."
docker-compose up -d

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
sleep 15

# Check if Kafka is running
if docker ps | grep -q kafka; then
    echo "✓ Kafka is running"
else
    echo "✗ Kafka failed to start"
    exit 1
fi

# Create topics
echo "Creating Kafka topics..."
chmod +x create_topics.sh
./create_topics.sh

echo ""
echo "=========================================="
echo "Kafka Services Started Successfully!"
echo "=========================================="
echo "Kafka Broker: $MACHINE_IP:9092"
echo "Kafka UI: http://$MACHINE_IP:8080"
echo ""
echo "To stop Kafka, run: docker-compose down"

