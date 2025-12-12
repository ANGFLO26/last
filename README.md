# FRAUD DETECTION PIPELINE - END-TO-END PROJECT

## 📋 Tổng quan

Dự án end-to-end về **Credit Card Fraud Detection** sử dụng:
- **Spark ML**: Huấn luyện model từ dữ liệu batch
- **Kafka**: Message broker cho streaming data
- **Spark Structured Streaming**: Real-time inference
- **Airflow**: Orchestration toàn bộ pipeline
- **Streamlit**: Real-time visualization

## 🎯 Yêu cầu Dự án

1. ✅ Chọn dataset: Credit Card Fraud Detection (Kaggle)
2. ✅ Chia dữ liệu: `train.csv` (199,365 records) và `stream.csv` (85,444 records)
3. ✅ Spark ML Training: RandomForest/GBTClassifier
4. ✅ Streaming Pipeline: Producer → Kafka → Spark → Kafka → Viewer
5. ✅ Airflow Orchestration: Điều khiển toàn bộ pipeline

## 🏗️ Kiến trúc - 3 MÁY RIÊNG BIỆT

Hệ thống gồm **3 máy độc lập**, mỗi máy tự quản lý services:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  MÁY 1: KAFKA   │    │  MÁY 2: SPARK   │    │ MÁY 3: AIRFLOW  │
│                 │    │                 │    │                 │
│ - Kafka Broker  │    │ - Spark Master  │    │ - Airflow       │
│ - Zookeeper     │    │ - Spark Workers │    │ - Producer      │
│ - Kafka UI      │    │ - Models Store  │    │ - Viewer        │
│                 │    │ - Checkpoints   │    │ - Scripts       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                        Network Communication
```

**LƯU Ý**: Không sử dụng SSH. Mỗi máy tự start services và communicate qua network.

## 📁 Cấu trúc Dự án

```
the_end/
├── data/                          # Data files
│   ├── train.csv                 # Training data (199,365 records)
│   └── stream.csv                 # Streaming data (85,444 records)
│
├── kafka_machine/                 # Máy 1: Kafka (độc lập)
│   ├── docker-compose.yml        # Docker Compose config
│   ├── create_topics.sh          # Script tạo Kafka topics
│   ├── start.sh                  # Start Kafka (chạy trên máy này)
│   └── stop.sh                   # Stop Kafka
│
├── spark_machine/                 # Máy 2: Spark (độc lập)
│   ├── start_spark_cluster.sh    # Start Spark Master & Workers
│   ├── stop_spark_cluster.sh     # Stop Spark
│   ├── verify_spark_cluster.sh   # Verify Spark ready
│   ├── start.sh                  # Start script (chạy trên máy này)
│   ├── stop.sh                   # Stop script
│   └── configs/
│       └── spark-defaults.conf   # Spark configuration
│
├── airflow_machine/               # Máy 3: Airflow (độc lập)
│   ├── dags/
│   │   └── fraud_detection_pipeline.py  # Airflow DAG chính
│   ├── scripts/
│   │   ├── train_model.py        # Spark ML training script
│   │   ├── streaming_inference.py # Spark streaming script
│   │   ├── producer.py           # Kafka producer
│   │   ├── viewer.py             # Streamlit viewer
│   │   └── verify_streaming_job.py # Verify Spark job
│   ├── utils/
│   │   └── spark_utils.py        # Spark utility functions
│   ├── start.sh                  # Start Airflow (chạy trên máy này)
│   ├── stop.sh                   # Stop Airflow
│   └── requirements.txt          # Python dependencies
│
├── .gitignore                     # Git ignore file
├── request.txt                    # Yêu cầu dự án gốc
└── README.md                      # File này
```

## 🚀 Quick Start

### Bước 1: Clone Repository

Trên **mỗi máy**, clone repository:

```bash
git clone <your-repo-url>
cd the_end
```

### Bước 2: Deploy Kafka Machine

**Trên Kafka Machine:**

```bash
cd kafka_machine

# Cài Docker nếu chưa có
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER
# Logout và login lại

# Start Kafka
chmod +x start.sh
./start.sh
```

**Script sẽ tự động:**
- Detect IP của máy
- Update `docker-compose.yml` với IP thực tế
- Start Kafka, Zookeeper, Kafka UI
- Tạo topics: `input_stream`, `prediction_output`

**Verify:**
```bash
# Check containers
docker ps

# Check Kafka UI
# Mở browser: http://kafka-machine-ip:8080
```

### Bước 3: Deploy Spark Machine

**Trên Spark Machine:**

```bash
cd spark_machine

# Cài đặt Spark (nếu chưa có)
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xzf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark

# Set environment
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
echo 'export SPARK_HOME=/opt/spark' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc

# Start Spark
chmod +x start.sh
./start.sh
```

**Script sẽ tự động:**
- Detect IP của máy
- Update configs với IP thực tế
- Copy configs vào `$SPARK_HOME/conf/`
- Tạo thư mục `/models` và `/checkpoints`
- Start Spark Master và Workers

**Verify:**
```bash
# Check Spark Web UI
# Mở browser: http://spark-machine-ip:8080

# Test connection
spark-submit --master spark://spark-machine-ip:7077 --version
```

### Bước 4: Deploy Airflow Machine

**Trên Airflow Machine:**

```bash
cd airflow_machine

# Cài dependencies
pip install -r requirements.txt

# ⚠️ QUAN TRỌNG: Cài Spark Client (SparkSubmitOperator cần spark-submit)
chmod +x install_spark_client.sh
./install_spark_client.sh

# Sau khi cài, thêm vào ~/.bashrc hoặc ~/.profile:
# export SPARK_HOME=/opt/spark
# export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
# source ~/.bashrc

# Verify Spark client
spark-submit --master spark://192.168.1.134:7077 --version

# Start Airflow
chmod +x start.sh
./start.sh
```

**Script sẽ:**
- Initialize Airflow database (lần đầu)
- Tạo admin user: `admin/admin`
- Hỏi IP của Kafka và Spark machines
- Update IPs trong DAG và scripts
- Start Airflow Scheduler và Webserver

**Verify:**
```bash
# Mở browser: http://airflow-machine-ip:8080
# Login: admin/admin
```

### Bước 5: Config Airflow Connection

1. Mở Airflow UI: `http://airflow-machine-ip:8080`
2. Login: `admin/admin`
3. **Admin → Connections → Add:**
   - **Conn Id**: `spark_default`
   - **Conn Type**: `Spark`
   - **Host**: `spark-machine-ip`
   - **Port**: `7077`
   - **Extra**: `{"master": "spark://spark-machine-ip:7077"}`

### Bước 6: Run Pipeline

1. Trong Airflow UI, tìm DAG `fraud_detection_pipeline`
2. Click **"Trigger DAG"**
3. Monitor tasks trong Graph View
4. Check logs nếu có lỗi

## 🔄 Pipeline Flow

```
1. verify_kafka_ready      → Check Kafka accessible (port 9092)
2. verify_spark_ready       → Check Spark accessible (port 7077, 8080)
3. verify_data_files        → Check train.csv và stream.csv exist
4. train_model              → Train Spark ML model (RandomForest/GBT)
5. start_spark_streaming    → Start Spark streaming job (long-running)
6. verify_streaming_running → Verify Spark streaming job RUNNING
7. start_producer           → Send data từ stream.csv vào Kafka
8. start_viewer             → Start Streamlit dashboard
```

**Data Flow:**
```
Producer → Kafka (input_stream) → Spark Streaming → Kafka (prediction_output) → Viewer
```

## 📝 Chi tiết Scripts

### 1. train_model.py
**Mục đích**: Huấn luyện Spark ML model từ `train.csv`

**Usage:**
```bash
spark-submit train_model.py \
    --input /path/to/train.csv \
    --output /models/fraud_detection_v1 \
    --model-type random_forest
```

**Output:**
- Model tại `/models/fraud_detection_v1/`
- Metrics tại `/models/fraud_detection_v1/metrics.json`

**Features:**
- Preprocessing: Handle missing values, feature scaling
- Models: RandomForest hoặc GBTClassifier
- Evaluation: AUC, Accuracy, Precision, Recall, F1

### 2. streaming_inference.py
**Mục đích**: Spark Structured Streaming để predict real-time từ Kafka

**Usage:**
```bash
spark-submit streaming_inference.py \
    --model-path /models/fraud_detection_v1 \
    --kafka-bootstrap kafka-machine-ip:9092 \
    --input-topic input_stream \
    --output-topic prediction_output
```

**Features:**
- Read từ Kafka topic `input_stream`
- Load trained model
- Predict và write vào Kafka topic `prediction_output`
- Checkpointing cho fault tolerance

### 3. producer.py
**Mục đích**: Gửi dữ liệu từ `stream.csv` vào Kafka

**Usage:**
```bash
python3 producer.py \
    --input /path/to/stream.csv \
    --kafka-bootstrap kafka-machine-ip:9092 \
    --topic input_stream \
    --rate 10
```

**Features:**
- Rate limiting: configurable messages/second
- Loop mode: `--loop` để gửi liên tục
- Error handling và retry logic

### 4. viewer.py
**Mục đích**: Streamlit app để visualization real-time

**Usage:**
```bash
streamlit run viewer.py --server.port 8501
```

**Features:**
- Real-time consumption từ Kafka
- Dashboard với metrics và charts
- Download predictions as CSV

### 5. verify_streaming_job.py
**Mục đích**: Verify Spark streaming job đã RUNNING

**Usage:**
```bash
python3 verify_streaming_job.py \
    --spark-ui-url http://spark-machine-ip:8080 \
    --job-name streaming \
    --timeout 600
```

## 🔧 Configuration

### IP Addresses

**Tự động detect:**
- Kafka Machine: `start.sh` tự động detect và update IP
- Spark Machine: `start.sh` tự động detect và update IP
- Airflow Machine: `start.sh` sẽ hỏi IP của Kafka và Spark machines

**Manual config (nếu cần):**
- Sửa IP trong `dags/fraud_detection_pipeline.py`
- Sửa IP trong các scripts nếu cần

### Network Requirements

**Kafka Machine:**
- Port 9092: Kafka Broker
- Port 2181: Zookeeper
- Port 8080: Kafka UI

**Spark Machine:**
- Port 7077: Spark Master
- Port 8080: Spark Web UI

**Airflow Machine:**
- Port 8080: Airflow Webserver
- Port 8501: Streamlit Viewer

**Firewall:**
```bash
# Trên mỗi máy, mở ports
sudo ufw allow 9092/tcp
sudo ufw allow 2181/tcp
sudo ufw allow 7077/tcp
sudo ufw allow 8080/tcp
sudo ufw allow 8501/tcp
```

### Airflow Connections

Config trong Airflow UI → Admin → Connections:

**Spark Connection:**
- Conn Id: `spark_default`
- Conn Type: `Spark`
- Host: `spark-machine-ip`
- Port: `7077`
- Extra: `{"master": "spark://spark-machine-ip:7077"}`

## 📦 Requirements

### Kafka Machine
- **OS**: Linux (Ubuntu/Debian recommended)
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **RAM**: 2GB+
- **Disk**: 10GB+

### Spark Machine
- **OS**: Linux (Ubuntu/Debian recommended)
- **Java**: 8+
- **Spark**: 3.5.0+
- **RAM**: 4GB+ (8GB recommended)
- **Disk**: 20GB+ (cho models và checkpoints)

### Airflow Machine
- **OS**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.8+
- **RAM**: 4GB+
- **Disk**: 10GB+

**Python Packages:**
```bash
pip install -r airflow_machine/requirements.txt
```

## 🐛 Troubleshooting

### Kafka không start
```bash
# Check Docker
docker ps
docker logs kafka

# Check ports
netstat -tulpn | grep 9092

# Restart
cd kafka_machine
docker-compose restart
```

### Spark không start
```bash
# Check Spark processes
jps | grep -E "Master|Worker"

# Check logs
tail -f $SPARK_HOME/logs/spark-*-master-*.out

# Check Web UI
curl http://spark-machine-ip:8080

# Restart
cd spark_machine
./stop.sh
./start.sh
```

### Airflow DAG không chạy
```bash
# Check DAG syntax
airflow dags list

# Check connections
# Airflow UI → Admin → Connections

# Check logs
airflow tasks logs fraud_detection_pipeline <task_id> <execution_date>

# Check Spark connection
spark-submit --master spark://spark-machine-ip:7077 --version
```

### Network connectivity issues
```bash
# Test từ Airflow machine
telnet kafka-machine-ip 9092
telnet spark-machine-ip 7077

# Test từ Spark machine
telnet kafka-machine-ip 9092

# Check firewall
sudo ufw status
```

### Model không load được
```bash
# Check model path exists trên Spark machine
ls -lh /models/fraud_detection_v1/

# Check permissions
sudo chmod -R 777 /models
```

## 📊 Dataset

- **Dataset**: Credit Card Fraud Detection
- **Source**: Kaggle
- **Problem**: Binary Classification (Fraud Detection)
- **Features**: 
  - Time, V1-V28 (PCA features), Amount
  - Class (0=Normal, 1=Fraud)
- **Train**: 199,365 records (199,030 normal, 334 fraud)
- **Stream**: 85,444 records (85,285 normal, 158 fraud)
- **Imbalanced**: ~0.17% fraud rate

## 🎯 Features

- ✅ **Không cần SSH**: Mỗi máy tự quản lý
- ✅ **Tự động config IP**: Scripts tự detect và update
- ✅ **Spark ML Training**: RandomForest/GBTClassifier với evaluation metrics
- ✅ **Real-time Streaming**: Spark Structured Streaming với checkpointing
- ✅ **Kafka Integration**: Topics cho input và output
- ✅ **Airflow Orchestration**: DAG với dependencies và retry logic
- ✅ **Real-time Visualization**: Streamlit dashboard với charts
- ✅ **Fault Tolerance**: Checkpointing cho streaming jobs
- ✅ **Error Handling**: Retry logic và error reporting

## 📝 Notes

1. **Mỗi máy độc lập**: Clone repository và chạy `start.sh` trên từng máy
2. **Không cần SSH**: Communication qua network (Kafka, Spark Master)
3. **IP Auto-detect**: Scripts tự động detect và config IP
4. **GitHub Ready**: Cấu trúc sẵn sàng để push lên GitHub
5. **Data Files**: `data/` folder có thể commit hoặc dùng Git LFS cho files lớn

## ✅ KIỂM TRA HỆ THỐNG

### Đã kiểm tra:
- ✅ **Python syntax**: Tất cả scripts không có lỗi syntax
- ✅ **Shell syntax**: Tất cả scripts không có lỗi syntax
- ✅ **DAG syntax**: Đúng Airflow 2.x format
- ✅ **Paths**: Đã sửa để flexible (hỗ trợ multiple locations)
- ✅ **IP Configuration**: Auto-detect và update
- ✅ **Dependencies**: Đầy đủ trong requirements.txt
- ✅ **No SSH**: Không sử dụng SSHOperator (đã loại bỏ)

### Vấn đề đã sửa:
1. ✅ DAG paths: `{{ dag.folder }}` → `{{ dag.dag_folder }}` (Airflow 2.x)
2. ✅ Data paths: Hỗ trợ multiple locations (tìm ở 3 nơi)
3. ✅ Kafka topics script: Hỗ trợ Docker container
4. ✅ Airflow logs: Tạo folder trước khi ghi
5. ✅ IP updates: Update trong cả scripts và utils
6. ✅ Spark config: Hỏi và update Kafka IP

### Checklist trước khi deploy:

**Kafka Machine:**
- [ ] Docker & Docker Compose installed
- [ ] Ports 9092, 2181, 8080 opened
- [ ] Run `./start.sh`
- [ ] Verify: `docker ps | grep kafka`
- [ ] Verify topics: `docker exec kafka kafka-topics.sh --list`

**Spark Machine:**
- [ ] Java 8+ và Spark 3.5.0+ installed
- [ ] SPARK_HOME set
- [ ] Ports 7077, 8080 opened
- [ ] Run `./start.sh` (sẽ hỏi Kafka IP)
- [ ] Verify: `jps | grep -E "Master|Worker"`
- [ ] Verify: `ls -ld /models /checkpoints`

**Airflow Machine:**
- [ ] Python 3.8+ installed
- [ ] Dependencies: `pip install -r requirements.txt`
- [ ] Ports 8080, 8501 opened
- [ ] Data files accessible (symlink: `airflow_machine/data` → `../../data`)
- [ ] Run `./start.sh` (sẽ hỏi Kafka và Spark IPs)
- [ ] Config Spark connection trong Airflow UI
- [ ] Verify DAG visible: `airflow dags list`

## 🐛 Troubleshooting

### Data files not found
- Verify symlink: `ls -la airflow_machine/data/`
- Or copy: `cp ../data/*.csv airflow_machine/data/`
- DAG sẽ tìm ở: `../../data/`, `../data/`, `data/`

### Spark connection failed
- Check Spark Master: `jps | grep Master`
- Test: `telnet spark-ip 7077`
- Check Airflow connection config (Host, Port, Extra)

### Kafka connection failed
- Check Kafka: `docker ps | grep kafka`
- Test: `telnet kafka-ip 9092`
- Check IP trong scripts đã đúng

### IPs không được update
- Verify `start.sh` đã chạy thành công
- Check: `grep -r "kafka-machine-ip" .`
- Re-run `start.sh` nếu cần

### Model path not found
- Check model exists: `ls -lh /models/fraud_detection_v1/`
- Check permissions: `sudo chmod -R 777 /models`
- Verify training task completed

## 🔗 Useful Links

- **Kafka UI**: `http://kafka-machine-ip:8080`
- **Spark Web UI**: `http://spark-machine-ip:8080`
- **Airflow UI**: `http://airflow-machine-ip:8080`
- **Streamlit Viewer**: `http://airflow-machine-ip:8501`

## 👥 Authors

Fraud Detection Team

## 📄 License

Educational Project

---

**Status**: ✅ **READY FOR DEPLOYMENT**

Hệ thống đã được kiểm tra kỹ và sẵn sàng để deploy lên 3 máy và test.
# last
