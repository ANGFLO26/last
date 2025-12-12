#!/bin/bash

# Script để config hệ thống với IPs cụ thể
# Kafka: 192.168.1.3
# Spark: 192.168.1.20
# Airflow: 192.168.1.21

echo "=========================================="
echo "Configuring System với IPs mới"
echo "=========================================="

KAFKA_IP="192.168.1.3"
SPARK_IP="192.168.1.20"
AIRFLOW_IP="192.168.1.21"

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

echo "IPs sẽ được config:"
echo "  Kafka Machine:   $KAFKA_IP"
echo "  Spark Machine:   $SPARK_IP"
echo "  Airflow Machine: $AIRFLOW_IP"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

# ========== 1. Update DAG default IPs ==========
echo ""
echo "1. Updating DAG default IPs..."
DAG_FILE="$PROJECT_ROOT/airflow_machine/dags/fraud_detection_pipeline.py"

if [ -f "$DAG_FILE" ]; then
    # Update Kafka IP default
    sed -i "s/KAFKA_IP = os.getenv(\"KAFKA_IP\", \"192.168.1.60\")/KAFKA_IP = os.getenv(\"KAFKA_IP\", \"$KAFKA_IP\")/g" "$DAG_FILE"
    
    # Update Spark IP default
    sed -i "s/SPARK_IP = os.getenv(\"SPARK_IP\", \"192.168.1.134\")/SPARK_IP = os.getenv(\"SPARK_IP\", \"$SPARK_IP\")/g" "$DAG_FILE"
    
    echo "  ✓ Updated DAG defaults"
else
    echo "  ✗ DAG file not found"
fi

# ========== 2. Update viewer.py default IP ==========
echo ""
echo "2. Updating viewer.py default IP..."
VIEWER_FILE="$PROJECT_ROOT/airflow_machine/scripts/viewer.py"

if [ -f "$VIEWER_FILE" ]; then
    sed -i "s/value=\"192.168.1.60:9092\"/value=\"$KAFKA_IP:9092\"/g" "$VIEWER_FILE"
    echo "  ✓ Updated viewer.py default"
else
    echo "  ✗ viewer.py not found"
fi

# ========== 3. Create .env file for Airflow ==========
echo ""
echo "3. Creating .env file for Airflow..."
ENV_FILE="$PROJECT_ROOT/airflow_machine/.env"

cat > "$ENV_FILE" << EOF
# Fraud Detection Pipeline Configuration
# Generated for deployment với IPs cụ thể

# IP Addresses
export KAFKA_IP=$KAFKA_IP
export KAFKA_PORT=9092
export SPARK_IP=$SPARK_IP
export SPARK_MASTER_PORT=7077
export SPARK_WEB_UI_PORT=8080

# Paths (auto-detected)
export FRAUD_SCRIPTS_DIR=$PROJECT_ROOT/airflow_machine/scripts
export FRAUD_UTILS_DIR=$PROJECT_ROOT/airflow_machine/utils
export FRAUD_DATA_DIR=$PROJECT_ROOT/data

# Spark Paths (on Spark machine)
export SPARK_DATA_DIR=/tmp/fraud_data
export SPARK_MODELS_DIR=/tmp/fraud_models
export SPARK_CHECKPOINTS_DIR=/checkpoints

# Kafka Topics
export KAFKA_INPUT_TOPIC=input_stream
export KAFKA_OUTPUT_TOPIC=prediction_output
EOF

echo "  ✓ Created .env file at $ENV_FILE"

# ========== 4. Create deployment checklist ==========
echo ""
echo "4. Creating deployment checklist..."
CHECKLIST_FILE="$PROJECT_ROOT/DEPLOYMENT_CHECKLIST_192.168.1.x.md"

cat > "$CHECKLIST_FILE" << 'CHECKLIST_EOF'
# CHECKLIST DEPLOYMENT VỚI IPs CỤ THỂ

## IPs Configuration
- **Kafka Machine:** 192.168.1.3
- **Spark Machine:** 192.168.1.20
- **Airflow Machine:** 192.168.1.21

---

## BƯỚC 1: KAFKA MACHINE (192.168.1.3)

### Trước khi start:
- [ ] Docker và Docker Compose đã được cài đặt
- [ ] Ports 9092, 2181, 8080 đã được mở trong firewall
- [ ] Repository đã được clone

### Start Kafka:
```bash
cd kafka_machine
./start.sh
```

### Verify:
- [ ] Kafka container running: `docker ps | grep kafka`
- [ ] Kafka accessible: `telnet 192.168.1.3 9092`
- [ ] Kafka UI accessible: `curl http://192.168.1.3:8080`
- [ ] Topics created: `docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:29092`

**Expected output:**
- Topics: `input_stream`, `prediction_output`

---

## BƯỚC 2: SPARK MACHINE (192.168.1.20)

### Trước khi start:
- [ ] Java 8+ đã được cài đặt
- [ ] Spark 3.5.0+ đã được cài đặt tại `/opt/spark`
- [ ] SPARK_HOME được set: `export SPARK_HOME=/opt/spark`
- [ ] Ports 7077, 8080 đã được mở trong firewall
- [ ] Repository đã được clone

### Prepare directories:
```bash
sudo mkdir -p /tmp/fraud_data /tmp/fraud_models /checkpoints
sudo chmod 777 /tmp/fraud_data /tmp/fraud_models /checkpoints
```

### Copy training data:
```bash
# Copy train.csv vào Spark machine
scp data/train.csv user@192.168.1.20:/tmp/fraud_data/train.csv
# Hoặc copy thủ công
```

### Start Spark:
```bash
cd spark_machine
# Khi hỏi Kafka IP, nhập: 192.168.1.3
./start.sh
```

### Verify:
- [ ] Spark Master running: `jps | grep Master`
- [ ] Spark Worker running: `jps | grep Worker`
- [ ] Spark Web UI accessible: `curl http://192.168.1.20:8080`
- [ ] Spark Master accessible: `telnet 192.168.1.20 7077`
- [ ] Training data exists: `ls -lh /tmp/fraud_data/train.csv`

---

## BƯỚC 3: AIRFLOW MACHINE (192.168.1.21)

### Trước khi start:
- [ ] Python 3.8+ đã được cài đặt
- [ ] Ports 8080, 8501 đã được mở trong firewall
- [ ] Repository đã được clone
- [ ] Data files tồn tại: `ls -lh data/stream.csv`

### Setup environment:
```bash
cd airflow_machine

# Source environment variables
source .env

# Hoặc set manually:
export KAFKA_IP=192.168.1.3
export SPARK_IP=192.168.1.20
export KAFKA_PORT=9092
export SPARK_MASTER_PORT=7077
export SPARK_WEB_UI_PORT=8080
```

### Install dependencies:
```bash
# Setup virtual environment
bash setup_venv.sh

# Activate venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install Spark client (nếu chưa có)
bash install_spark_client.sh
```

### Verify Spark connection:
```bash
# Test Spark connection
spark-submit --master spark://192.168.1.20:7077 --version
```

### Start Airflow:
```bash
cd airflow_machine
source venv/bin/activate
source .env  # Load IPs
bash start.sh
```

### Configure Airflow Connection:
1. Mở browser: `http://192.168.1.21:8080`
2. Login: `admin/admin`
3. **Admin → Connections → Add/Edit:**
   - **Conn Id:** `spark_default`
   - **Conn Type:** `Spark`
   - **Host:** `192.168.1.20`
   - **Port:** `7077`
   - **Extra:** `{"master": "spark://192.168.1.20:7077"}`

### Verify:
- [ ] Airflow UI accessible: `http://192.168.1.21:8080`
- [ ] DAG `fraud_detection_pipeline` visible
- [ ] Spark connection configured
- [ ] Can connect to Kafka: `telnet 192.168.1.3 9092`
- [ ] Can connect to Spark: `telnet 192.168.1.20 7077`

---

## BƯỚC 4: RUN PIPELINE

### Trigger DAG:
1. Mở Airflow UI: `http://192.168.1.21:8080`
2. Toggle ON DAG `fraud_detection_pipeline`
3. Click **"Trigger DAG"**

### Monitor Tasks:
- [ ] `verify_scripts` → SUCCESS
- [ ] `verify_kafka_ready` → SUCCESS (check 192.168.1.3:9092)
- [ ] `verify_spark_ready` → SUCCESS (check 192.168.1.20:7077)
- [ ] `verify_data_files` → SUCCESS
- [ ] `train_model` → SUCCESS (có thể mất 5-10 phút)
- [ ] `start_spark_streaming` → SUCCESS (job RUNNING)
- [ ] `verify_streaming_running` → SUCCESS
- [ ] `start_producer` → SUCCESS
- [ ] `start_viewer` → SUCCESS

### Verify Results:
- [ ] Model created: `ls -lh /tmp/fraud_models/fraud_detection_v1/` (trên Spark machine)
- [ ] Metrics file: `cat /tmp/fraud_models/fraud_detection_v1/metrics.json`
- [ ] Spark streaming job RUNNING: `http://192.168.1.20:8080` → Streaming tab
- [ ] Messages in Kafka: `docker exec kafka kafka-console-consumer.sh --bootstrap-server localhost:29092 --topic prediction_output --from-beginning --max-messages 10`
- [ ] Viewer accessible: `http://192.168.1.21:8501`

---

## TROUBLESHOOTING

### Nếu không connect được Kafka (192.168.1.3):
```bash
# Test từ Airflow machine
telnet 192.168.1.3 9092

# Check firewall trên Kafka machine
sudo ufw status
sudo ufw allow 9092/tcp
```

### Nếu không connect được Spark (192.168.1.20):
```bash
# Test từ Airflow machine
telnet 192.168.1.20 7077
curl http://192.168.1.20:8080

# Check firewall trên Spark machine
sudo ufw status
sudo ufw allow 7077/tcp
sudo ufw allow 8080/tcp
```

### Nếu DAG không thấy IPs đúng:
```bash
# Source .env file trước khi start Airflow
cd airflow_machine
source .env
bash start.sh
```

### Nếu model không được lưu:
```bash
# Trên Spark machine, check permissions
ls -ld /tmp/fraud_models
sudo chmod 777 /tmp/fraud_models
```

---

## QUICK TEST COMMANDS

### Test Kafka:
```bash
# Từ Airflow machine
telnet 192.168.1.3 9092
```

### Test Spark:
```bash
# Từ Airflow machine
telnet 192.168.1.20 7077
curl http://192.168.1.20:8080
spark-submit --master spark://192.168.1.20:7077 --version
```

### Test Network:
```bash
# Từ Airflow machine
ping 192.168.1.3  # Kafka
ping 192.168.1.20  # Spark
```

---

## EXPECTED ENDPOINTS

- **Kafka Broker:** 192.168.1.3:9092
- **Kafka UI:** http://192.168.1.3:8080
- **Spark Master:** spark://192.168.1.20:7077
- **Spark Web UI:** http://192.168.1.20:8080
- **Airflow UI:** http://192.168.1.21:8080
- **Streamlit Viewer:** http://192.168.1.21:8501

CHECKLIST_EOF

echo "  ✓ Created checklist at $CHECKLIST_FILE"

echo ""
echo "=========================================="
echo "Configuration Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review checklist: cat $CHECKLIST_FILE"
echo "2. Deploy theo thứ tự: Kafka → Spark → Airflow"
echo "3. Source .env file trên Airflow machine: source airflow_machine/.env"
echo ""

