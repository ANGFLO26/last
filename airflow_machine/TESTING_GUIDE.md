# Hướng dẫn Test Airflow DAG

## ✅ Giải thích về cảnh báo

### 1. SequentialExecutor + SQLite
- **Hiện tại:** Đang sử dụng `SequentialExecutor` với SQLite
- **Lý do:** SQLite không hỗ trợ concurrent writes tốt, nên chỉ tương thích với SequentialExecutor
- **Cảnh báo:** Đây là cảnh báo thông tin, **KHÔNG phải lỗi**
- **Phù hợp:** Hoàn toàn OK cho dev/testing
- **Production:** Nếu cần chạy song song nhiều tasks, nên:
  - Dùng PostgreSQL/MySQL + LocalExecutor
  - Hoặc CeleryExecutor với Redis/RabbitMQ

### 2. SQLite Database
- **Lưu ý:** SQLite vẫn được sử dụng cho dev/testing
- **Cảnh báo:** Đây là cảnh báo thông tin, không phải lỗi
- **Production:** Nên dùng PostgreSQL hoặc MySQL (có thể cấu hình sau)

## 🔄 Restart Airflow để áp dụng thay đổi

```bash
cd airflow_machine
source venv/bin/activate
export AIRFLOW_HOME=$(pwd)

# Dừng Airflow
bash stop.sh

# Khởi động lại
bash start.sh
```

## 🧪 Test DAG: fraud_detection_pipeline

### Bước 1: Kiểm tra DAG trong UI

1. Truy cập: `http://192.168.1.50:8080`
2. Đăng nhập: `admin` / `admin`
3. Tìm DAG `fraud_detection_pipeline`
4. Kiểm tra DAG không có lỗi (không có biểu tượng cảnh báo đỏ)

### Bước 2: Kiểm tra Connections

1. Vào **Admin → Connections**
2. Tìm hoặc tạo connection với ID: `spark_default`
3. Nếu chưa có, tạo mới:
   - **Conn Id:** `spark_default`
   - **Conn Type:** `Spark`
   - **Host:** `192.168.1.134`
   - **Port:** `7077`
   - **Extra:** `{"master": "spark://192.168.1.134:7077"}`

### Bước 3: Kiểm tra Services

**Kiểm tra Kafka:**
```bash
# Từ Airflow machine
telnet 192.168.1.60 9092
# Hoặc
nc -zv 192.168.1.60 9092
```

**Kiểm tra Spark:**
```bash
# Từ Airflow machine
curl http://192.168.1.134:8080
# Hoặc
curl http://192.168.1.134:7077
```

### Bước 4: Kích hoạt DAG

1. Trong Airflow UI, tìm DAG `fraud_detection_pipeline`
2. Toggle switch từ OFF → ON (bên trái tên DAG)
3. DAG sẽ chuyển sang trạng thái "Active"

### Bước 5: Trigger DAG Run

**Cách 1: Từ UI**
1. Click vào tên DAG `fraud_detection_pipeline`
2. Click nút **"Play"** (▶️) ở góc trên bên phải
3. Chọn **"Trigger DAG"**
4. Xác nhận trigger

**Cách 2: Từ Command Line**
```bash
cd airflow_machine
source venv/bin/activate
export AIRFLOW_HOME=$(pwd)

# Trigger DAG
airflow dags trigger fraud_detection_pipeline
```

### Bước 6: Theo dõi DAG Run

1. **Trong UI:**
   - Click vào DAG name
   - Xem Graph View để thấy flow của tasks
   - Xem Tree View để thấy lịch sử runs
   - Click vào task để xem logs

2. **Từ Command Line:**
```bash
# Xem danh sách DAG runs
airflow dags list-runs -d fraud_detection_pipeline

# Xem task instances
airflow tasks list fraud_detection_pipeline

# Xem logs của một task
airflow tasks logs fraud_detection_pipeline <task_id> <execution_date>
```

### Bước 7: Kiểm tra từng Task

DAG `fraud_detection_pipeline` có các tasks theo thứ tự:

1. **verify_kafka_ready** - Kiểm tra Kafka accessible
2. **verify_spark_ready** - Kiểm tra Spark Master accessible
3. **verify_data_files** - Kiểm tra data files tồn tại
4. **train_model** - Train ML model với Spark
5. **start_spark_streaming** - Start Spark streaming job
6. **verify_streaming_running** - Verify streaming job đang chạy
7. **start_producer** - Start Kafka producer
8. **start_viewer** - Start Streamlit viewer

**Kiểm tra logs:**
- Click vào từng task trong Graph View
- Xem logs để kiểm tra output
- Kiểm tra status (success/failed)

## 🔍 Troubleshooting

### Task bị failed

1. **Xem logs:**
   - Click vào task failed
   - Xem tab "Log" để biết lỗi

2. **Các lỗi thường gặp:**

   **Lỗi: "Kafka is not accessible"**
   - Kiểm tra Kafka đang chạy: `telnet 192.168.1.60 9092`
   - Kiểm tra firewall: `sudo ufw status`
   - Kiểm tra IP đúng trong DAG

   **Lỗi: "Spark Master is not accessible"**
   - Kiểm tra Spark đang chạy: `curl http://192.168.1.134:8080`
   - Kiểm tra connection `spark_default` trong Airflow
   - Kiểm tra IP đúng trong DAG

   **Lỗi: "Data files not found"**
   - Kiểm tra file tồn tại: `ls -lh data/train.csv data/stream.csv`
   - Kiểm tra đường dẫn trong DAG đúng

   **Lỗi: "Connection refused" trong SparkSubmitOperator**
   - Kiểm tra Spark connection trong Airflow UI
   - Kiểm tra Spark Master đang chạy
   - Kiểm tra network connectivity

### DAG không chạy

1. **Kiểm tra DAG active:**
   - Toggle switch phải ON (màu xanh)

2. **Kiểm tra Scheduler:**
   ```bash
   # Xem scheduler logs
   tail -f logs/scheduler.log
   
   # Kiểm tra scheduler đang chạy
   ps aux | grep "airflow scheduler"
   ```

3. **Kiểm tra DAG syntax:**
   ```bash
   cd airflow_machine
   source venv/bin/activate
   export AIRFLOW_HOME=$(pwd)
   
   # List DAGs
   airflow dags list
   
   # Kiểm tra DAG cụ thể
   airflow dags show fraud_detection_pipeline
   ```

## 📊 Kiểm tra kết quả

### Sau khi DAG chạy thành công:

1. **Model được train:**
   - Kiểm tra model file trên Spark machine: `ls -lh /models/fraud_detection_v1/`

2. **Streaming job đang chạy:**
   - Kiểm tra Spark UI: `http://192.168.1.134:8080`
   - Tìm streaming job trong "Running Applications"

3. **Kafka messages:**
   - Kiểm tra Kafka topics: `kafka-topics.sh --list --bootstrap-server 192.168.1.60:9092`
   - Kiểm tra messages: `kafka-console-consumer.sh --bootstrap-server 192.168.1.60:9092 --topic prediction_output --from-beginning`

4. **Streamlit Viewer:**
   - Truy cập: `http://192.168.1.50:8501`
   - Xem real-time predictions

## 🎯 Quick Test Commands

```bash
# 1. Kích hoạt venv
cd airflow_machine
source venv/bin/activate
export AIRFLOW_HOME=$(pwd)

# 2. Kiểm tra DAG
airflow dags list | grep fraud_detection

# 3. Trigger DAG
airflow dags trigger fraud_detection_pipeline

# 4. Xem DAG runs
airflow dags list-runs -d fraud_detection_pipeline --state running

# 5. Xem logs
tail -f logs/scheduler.log
```

## ✅ Checklist Test

- [ ] Airflow UI accessible
- [ ] DAG `fraud_detection_pipeline` hiển thị
- [ ] DAG không có lỗi (no broken DAG)
- [ ] Connection `spark_default` đã được tạo
- [ ] Kafka accessible (192.168.1.60:9092)
- [ ] Spark Master accessible (192.168.1.134:7077)
- [ ] Data files tồn tại
- [ ] DAG được toggle ON
- [ ] DAG run được trigger thành công
- [ ] Tất cả tasks chạy thành công
- [ ] Model được train
- [ ] Streaming job đang chạy
- [ ] Streamlit viewer accessible
