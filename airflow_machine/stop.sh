#!/bin/bash

# Script để stop Airflow trên Airflow Machine

echo "Stopping Airflow Services..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Stop Scheduler
if [ -f ".scheduler.pid" ]; then
    SCHEDULER_PID=$(cat .scheduler.pid)
    if ps -p $SCHEDULER_PID > /dev/null; then
        echo "Stopping Scheduler (PID: $SCHEDULER_PID)..."
        kill $SCHEDULER_PID
        rm .scheduler.pid
    fi
fi

# Stop Webserver
pkill -f "airflow webserver"

echo "Airflow Services Stopped"

