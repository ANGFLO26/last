# KIỂM TRA HỆ THỐNG - CHECKLIST ĐÁP ỨNG YÊU CẦU

## 📋 YÊU CẦU DỰ ÁN

### ✅ YÊU CẦU 1: Chọn Dataset từ Kaggle
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

- **Dataset:** Credit Card Fraud Detection
- **Nguồn:** Kaggle
- **Vấn đề:** Binary Classification (Fraud Detection)
- **Features:** Time, V1-V28 (PCA features), Amount, Class
- **Kích thước:** 
  - Train: 199,365 records
  - Stream: 85,444 records

**Vị trí file:**
- `data/train.csv` - Training data
- `data/stream.csv` - Streaming data

**Kiểm tra:**
```bash
# Kiểm tra files tồn tại
ls -lh data/train.csv data/stream.csv

# Kiểm tra số dòng
wc -l data/train.csv data/stream.csv
```

---

### ✅ YÊU CẦU 2: Chia dữ liệu thành 2 phần
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

- **Phần 1 (Training):** `train.csv` - 199,365 records
- **Phần 2 (Streaming):** `stream.csv` - 85,444 records

**Kiểm tra:**
```bash
# Kiểm tra train.csv
head -5 data/train.csv
tail -5 data/train.csv

# Kiểm tra stream.csv
head -5 data/stream.csv
tail -5 data/stream.csv

# Kiểm tra class distribution
grep -c ",1$" data/train.csv  # Fraud cases
grep -c ",0$" data/train.csv  # Normal cases
```

---

### ✅ YÊU CẦU 3: Spark ML Training
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

**Script:** `airflow_machine/scripts/train_model.py`

**Chức năng:**
- ✅ Đọc dữ liệu từ CSV
- ✅ Preprocessing (handle missing values, feature scaling)
- ✅ Training với RandomForest hoặc GBTClassifier
- ✅ Evaluation (AUC, Accuracy, Precision, Recall, F1)
- ✅ Lưu model và metrics

**Model được lưu ở đâu:**
- **Path:** `/tmp/fraud_models/fraud_detection_v1` (trên Spark machine)
- **Format:** Spark ML PipelineModel
- **Files trong model folder:**
  - `metadata/` - Model metadata
  - `stages/` - Pipeline stages (VectorAssembler, StandardScaler, Model)
  - `metrics.json` - Training metrics

**Kiểm tra:**
```bash
# Trên Spark machine
ls -lh /tmp/fraud_models/fraud_detection_v1/
cat /tmp/fraud_models/fraud_detection_v1/metrics.json
```

**Task trong DAG:** `train_model` (SparkSubmitOperator)

---

### ✅ YÊU CẦU 4: Streaming Pipeline
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

#### 4.1. Producer (Mô phỏng streaming)
**Script:** `airflow_machine/scripts/producer.py`

**Chức năng:**
- ✅ Đọc `stream.csv`
- ✅ Gửi messages vào Kafka topic `input_stream`
- ✅ Rate limiting (configurable)
- ✅ JSON format

**Task trong DAG:** `start_producer` (BashOperator)

#### 4.2. Spark Streaming (Đọc và Predict)
**Script:** `airflow_machine/scripts/streaming_inference.py`

**Chức năng:**
- ✅ Đọc từ Kafka topic `input_stream`
- ✅ Load trained model từ `/tmp/fraud_models/fraud_detection_v1`
- ✅ Predict với model
- ✅ Ghi kết quả vào Kafka topic `prediction_output`
- ✅ Checkpointing cho fault tolerance

**Task trong DAG:** `start_spark_streaming` (SparkSubmitOperator)

#### 4.3. Visualization
**Script:** `airflow_machine/scripts/viewer.py`

**Chức năng:**
- ✅ Đọc predictions từ Kafka topic `prediction_output`
- ✅ Real-time dashboard với Streamlit
- ✅ Metrics: Total, Fraud, Normal, Fraud Rate
- ✅ Charts: Pie chart, Timeline
- ✅ Download predictions as CSV

**Task trong DAG:** `start_viewer` (BashOperator)

**Kiểm tra:**
```bash
# Kiểm tra producer
python3 airflow_machine/scripts/producer.py --help

# Kiểm tra streaming script
python3 airflow_machine/scripts/streaming_inference.py --help

# Kiểm tra viewer
streamlit run airflow_machine/scripts/viewer.py --help
```

---

### ⚠️ YÊU CẦU 5: Airflow Orchestration
**Trạng thái:** ⚠️ **MỘT PHẦN ĐÁP ỨNG**

#### 5.1. Khởi động Kafka (Docker)
**Trạng thái:** ⚠️ **CHỈ VERIFY, KHÔNG START**

**Hiện tại:**
- Task `verify_kafka_ready` chỉ kiểm tra Kafka accessible
- Kafka phải được start thủ công trên Kafka machine: `cd kafka_machine && ./start.sh`

**Cần bổ sung:**
- Task để start Kafka Docker containers (nếu cần)
- Hoặc giữ nguyên như hiện tại (manual start) vì Kafka là long-running service

**Kiểm tra:**
```bash
# Trên Kafka machine
cd kafka_machine
./start.sh

# Verify
docker ps | grep kafka
curl http://kafka-machine-ip:8080  # Kafka UI
```

#### 5.2. Chạy Spark Server
**Trạng thái:** ⚠️ **CHỈ VERIFY, KHÔNG START**

**Hiện tại:**
- Task `verify_spark_ready` chỉ kiểm tra Spark Master accessible
- Spark phải được start thủ công trên Spark machine: `cd spark_machine && ./start.sh`

**Cần bổ sung:**
- Task để start Spark Master và Workers (nếu cần)
- Hoặc giữ nguyên như hiện tại (manual start) vì Spark là long-running service

**Kiểm tra:**
```bash
# Trên Spark machine
cd spark_machine
./start.sh

# Verify
jps | grep -E "Master|Worker"
curl http://spark-machine-ip:8080  # Spark Web UI
```

#### 5.3. Chạy Streaming Simulation
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

**Task:** `start_producer` - Chạy producer.py để gửi data vào Kafka

#### 5.4. Submit Code Training
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

**Task:** `train_model` - Submit train_model.py lên Spark cluster

#### 5.5. Submit Code Prediction
**Trạng thái:** ✅ **ĐÃ ĐÁP ỨNG**

**Task:** `start_spark_streaming` - Submit streaming_inference.py lên Spark cluster

---

## 📊 TỔNG KẾT ĐÁP ỨNG YÊU CẦU

| Yêu cầu | Trạng thái | Ghi chú |
|---------|-----------|---------|
| 1. Dataset từ Kaggle | ✅ | Credit Card Fraud Detection |
| 2. Chia dữ liệu train/stream | ✅ | train.csv và stream.csv |
| 3. Spark ML Training | ✅ | train_model.py với RandomForest/GBT |
| 4. Streaming Pipeline | ✅ | Producer → Kafka → Spark → Kafka → Viewer |
| 5.1. Start Kafka (Docker) | ⚠️ | Chỉ verify, không start tự động |
| 5.2. Start Spark Server | ⚠️ | Chỉ verify, không start tự động |
| 5.3. Run Streaming Simulation | ✅ | start_producer task |
| 5.4. Submit Training Code | ✅ | train_model task |
| 5.5. Submit Prediction Code | ✅ | start_spark_streaming task |

**Tổng điểm:** 7/9 yêu cầu đã đáp ứng đầy đủ, 2 yêu cầu chỉ verify (có thể chấp nhận vì services là long-running)

---

## 📍 MODEL ĐƯỢC LƯU Ở ĐÂU?

### Vị trí Model sau khi Training:

**Trên Spark Machine:**
```
/tmp/fraud_models/fraud_detection_v1/
├── metadata/
│   ├── metadata/
│   └── ...
├── stages/
│   ├── 0_VectorAssembler_xxx/
│   ├── 1_StandardScaler_xxx/
│   └── 2_RandomForestClassifier_xxx/
└── metrics.json
```

**Path trong DAG:**
```python
application_args=[
    '--output', f'{SPARK_MODELS_DIR}/fraud_detection_v1',
]
# Default: /tmp/fraud_models/fraud_detection_v1
```

**Kiểm tra Model:**
```bash
# Trên Spark machine
ls -lh /tmp/fraud_models/fraud_detection_v1/
cat /tmp/fraud_models/fraud_detection_v1/metrics.json

# Kiểm tra model có thể load được không
python3 -c "
from pyspark.ml import PipelineModel
model = PipelineModel.load('/tmp/fraud_models/fraud_detection_v1')
print('Model loaded successfully!')
"
```

**Model được sử dụng ở đâu:**
- Streaming inference script load model từ path này:
  ```python
  --model-path file:///tmp/fraud_models/fraud_detection_v1
  ```

---

## 🔍 HƯỚNG DẪN KIỂM TRA TỪNG QUÁ TRÌNH

### 1. Kiểm tra Dataset

```bash
# Kiểm tra files tồn tại
cd /home/phanvantai/Documents/four_years/bigdata/the_end
ls -lh data/*.csv

# Kiểm tra số dòng
wc -l data/train.csv data/stream.csv

# Kiểm tra header
head -1 data/train.csv
head -1 data/stream.csv

# Kiểm tra class distribution
echo "Train - Fraud cases:"
grep -c ",1$" data/train.csv
echo "Train - Normal cases:"
grep -c ",0$" data/train.csv
```

**Kết quả mong đợi:**
- train.csv: ~199,365 dòng
- stream.csv: ~85,444 dòng
- Có header với các columns: Time, V1-V28, Amount, Class

---

### 2. Kiểm tra Kafka

```bash
# Trên Kafka machine
cd kafka_machine

# Start Kafka
./start.sh

# Kiểm tra containers
docker ps | grep -E "kafka|zookeeper"

# Kiểm tra topics
docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:29092

# Kiểm tra Kafka UI
curl http://localhost:8080

# Test producer (từ Airflow machine)
python3 -c "
from kafka import KafkaProducer
import json
producer = KafkaProducer(
    bootstrap_servers='kafka-machine-ip:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
producer.send('input_stream', {'test': 'data'})
producer.flush()
print('Message sent successfully!')
"
```

**Kết quả mong đợi:**
- Kafka containers running
- Topics: `input_stream`, `prediction_output`
- Kafka UI accessible
- Producer có thể gửi messages

---

### 3. Kiểm tra Spark Cluster

```bash
# Trên Spark machine
cd spark_machine

# Start Spark
./start.sh

# Kiểm tra processes
jps | grep -E "Master|Worker"

# Kiểm tra Spark Web UI
curl http://localhost:8080

# Test Spark connection (từ Airflow machine)
spark-submit --master spark://spark-machine-ip:7077 --version

# Kiểm tra thư mục models và checkpoints
ls -ld /tmp/fraud_data /tmp/fraud_models /checkpoints
```

**Kết quả mong đợi:**
- Spark Master và Worker processes running
- Spark Web UI accessible
- Có thể connect từ Airflow machine
- Thư mục models và checkpoints tồn tại

---

### 4. Kiểm tra Training Process

```bash
# Trên Airflow machine
cd airflow_machine

# Test training script locally (nếu có Spark local)
spark-submit scripts/train_model.py \
    --input /tmp/fraud_data/train.csv \
    --output /tmp/fraud_models/test_model

# Hoặc chạy qua Airflow DAG
# Trigger DAG → Task: train_model

# Sau khi training, kiểm tra model
# Trên Spark machine:
ls -lh /tmp/fraud_models/fraud_detection_v1/
cat /tmp/fraud_models/fraud_detection_v1/metrics.json
```

**Kết quả mong đợi:**
- Training job chạy thành công
- Model được lưu tại `/tmp/fraud_models/fraud_detection_v1/`
- File `metrics.json` có các metrics: AUC, Accuracy, Precision, Recall, F1

**Kiểm tra Metrics:**
```bash
cat /tmp/fraud_models/fraud_detection_v1/metrics.json
```

**Metrics mong đợi:**
- AUC: > 0.90 (tốt)
- Accuracy: > 0.99 (do imbalanced data)
- Precision, Recall, F1: hợp lý

---

### 5. Kiểm tra Streaming Process

#### 5.1. Kiểm tra Producer

```bash
# Trên Airflow machine
cd airflow_machine

# Test producer (không gửi thực tế)
python3 scripts/producer.py --help

# Test producer với một vài records
head -10 data/stream.csv > /tmp/test_stream.csv
python3 scripts/producer.py \
    --input /tmp/test_stream.csv \
    --kafka-bootstrap kafka-machine-ip:9092 \
    --topic input_stream \
    --rate 1

# Kiểm tra messages trong Kafka
# Trên Kafka machine:
docker exec kafka kafka-console-consumer.sh \
    --bootstrap-server localhost:29092 \
    --topic input_stream \
    --from-beginning \
    --max-messages 5
```

**Kết quả mong đợi:**
- Producer gửi messages thành công
- Messages có format JSON đúng
- Messages xuất hiện trong Kafka topic

#### 5.2. Kiểm tra Spark Streaming

```bash
# Trên Airflow machine
# Trigger DAG → Task: start_spark_streaming

# Kiểm tra Spark Web UI
# Mở browser: http://spark-machine-ip:8080
# Xem tab "Streaming" → Job "FraudDetectionStreaming"

# Kiểm tra logs
# Trong Airflow UI → Task logs → start_spark_streaming

# Kiểm tra checkpoint
# Trên Spark machine:
ls -lh /checkpoints/streaming_inference/
```

**Kết quả mong đợi:**
- Spark streaming job RUNNING
- Đọc messages từ Kafka topic `input_stream`
- Predict và ghi vào Kafka topic `prediction_output`
- Checkpoint được tạo

#### 5.3. Kiểm tra Predictions trong Kafka

```bash
# Trên Kafka machine
docker exec kafka kafka-console-consumer.sh \
    --bootstrap-server localhost:29092 \
    --topic prediction_output \
    --from-beginning \
    --max-messages 10
```

**Kết quả mong đợi:**
- Messages có format JSON với các fields:
  - `transaction_id`
  - `timestamp`
  - `prediction` (0 hoặc 1)
  - `probability`
  - `model_version`
  - `prediction_timestamp`

---

### 6. Kiểm tra Visualization

```bash
# Trên Airflow machine
cd airflow_machine

# Start viewer
streamlit run scripts/viewer.py --server.port 8501

# Mở browser: http://airflow-machine-ip:8501

# Hoặc trigger DAG → Task: start_viewer
```

**Kiểm tra Dashboard:**
- ✅ Total Predictions counter tăng dần
- ✅ Fraud Detected counter hiển thị đúng
- ✅ Pie chart hiển thị distribution
- ✅ Timeline chart hiển thị predictions theo thời gian
- ✅ Table hiển thị recent predictions
- ✅ Download CSV button hoạt động

---

### 7. Kiểm tra Toàn bộ Pipeline qua Airflow

```bash
# Trên Airflow machine
cd airflow_machine

# Start Airflow
./start.sh

# Mở browser: http://airflow-machine-ip:8080
# Login: admin/admin

# Trigger DAG: fraud_detection_pipeline

# Monitor tasks:
# 1. verify_scripts → SUCCESS
# 2. verify_kafka_ready → SUCCESS
# 3. verify_spark_ready → SUCCESS
# 4. verify_data_files → SUCCESS
# 5. train_model → SUCCESS (có thể mất 5-10 phút)
# 6. start_spark_streaming → SUCCESS (job RUNNING)
# 7. verify_streaming_running → SUCCESS
# 8. start_producer → SUCCESS (gửi messages)
# 9. start_viewer → SUCCESS (dashboard accessible)
```

**Kiểm tra Logs:**
- Click vào từng task → View Log
- Kiểm tra có lỗi không
- Kiểm tra output messages

---

## 🐛 TROUBLESHOOTING CHECKLIST

### Nếu Training fail:
- [ ] Kiểm tra train.csv tồn tại trên Spark machine tại `/tmp/fraud_data/`
- [ ] Kiểm tra Spark cluster đang running
- [ ] Kiểm tra permissions trên `/tmp/fraud_models/`
- [ ] Xem logs trong Airflow UI

### Nếu Streaming fail:
- [ ] Kiểm tra model đã được train chưa
- [ ] Kiểm tra Kafka đang running
- [ ] Kiểm tra Spark streaming job RUNNING
- [ ] Kiểm tra checkpoint directory có quyền write

### Nếu Producer fail:
- [ ] Kiểm tra stream.csv tồn tại
- [ ] Kiểm tra Kafka accessible
- [ ] Kiểm tra topic `input_stream` đã được tạo

### Nếu Viewer không hiển thị data:
- [ ] Kiểm tra Spark streaming đang chạy
- [ ] Kiểm tra Producer đã gửi messages
- [ ] Kiểm tra Kafka topic `prediction_output` có messages
- [ ] Kiểm tra Kafka connection trong viewer.py

---

## ✅ CHECKLIST TRƯỚC KHI DEMO

- [ ] Dataset đã được chia thành train.csv và stream.csv
- [ ] Kafka đã được start và topics đã được tạo
- [ ] Spark cluster đã được start
- [ ] Airflow đã được start và DAG visible
- [ ] Airflow Connection `spark_default` đã được config
- [ ] train.csv đã được copy lên Spark machine tại `/tmp/fraud_data/`
- [ ] Thư mục `/tmp/fraud_models/` và `/checkpoints/` đã được tạo với permissions đúng
- [ ] Network connectivity giữa các machines OK
- [ ] Firewall rules đã được mở

---

## 📝 GHI CHÚ QUAN TRỌNG

1. **Kafka và Spark là long-running services:** Nên start thủ công trước khi chạy pipeline, không cần start tự động trong DAG.

2. **Model path:** Model được lưu trên Spark machine tại `/tmp/fraud_models/fraud_detection_v1/`. Đảm bảo path này có quyền write.

3. **Data files:** 
   - `train.csv` phải ở trên Spark machine tại `/tmp/fraud_data/train.csv`
   - `stream.csv` phải ở trên Airflow machine tại `data/stream.csv`

4. **Checkpoints:** Spark streaming checkpoint tại `/checkpoints/streaming_inference/` trên Spark machine.

5. **Network:** Đảm bảo các machines có thể communicate với nhau qua network.

