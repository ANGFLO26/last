#!/bin/bash

# Script để stop Kafka trên Kafka Machine

echo "Stopping Kafka Services..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

docker-compose down

echo "Kafka Services Stopped"

