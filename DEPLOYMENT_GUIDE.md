# HƯỚNG DẪN DEPLOY HỆ THỐNG LÊN MÁY MỚI

## 📋 TỔNG QUAN

Hướng dẫn này giúp bạn deploy hệ thống Fraud Detection Pipeline lên các máy mới mà không gặp lỗi về paths và permissions.

## 🔍 CÁC VẤN ĐỀ ĐÃ ĐƯỢC GIẢI QUYẾT

### ✅ Đã sửa:
1. **Hardcoded paths** → Sử dụng relative paths và environment variables
2. **File upload** → SparkSubmitOperator tự động upload files
3. **Dependencies** → Sử dụng `files` parameter để upload utils
4. **IP addresses** → Có thể config qua environment variables
5. **Validation** → Thêm task verify scripts tồn tại

## 🚀 QUY TRÌNH DEPLOY

### Bước 1: Clone Repository

Trên **mỗi máy**, clone repository:

```bash
git clone <your-repo-url>
cd the_end
```

### Bước 2: Setup Airflow Machine

**Trên Airflow Machine:**

```bash
cd airflow_machine

# 1. Chạy script setup tự động
bash setup_deployment.sh
```

Script sẽ:
- Tự động detect paths
- Hỏi IP addresses của Kafka và Spark machines
- Tạo file `.env` với configuration
- Verify scripts và data files tồn tại

**Hoặc setup thủ công:**

```bash
# Set environment variables
export KAFKA_IP=192.168.1.60
export KAFKA_PORT=9092
export SPARK_IP=192.168.1.134
export SPARK_MASTER_PORT=7077
export SPARK_WEB_UI_PORT=8080

# Paths (tự động detect từ DAG folder)
export FRAUD_SCRIPTS_DIR=/path/to/airflow_machine/scripts
export FRAUD_UTILS_DIR=/path/to/airflow_machine/utils
export FRAUD_DATA_DIR=/path/to/data

# Spark paths (trên Spark machine)
export SPARK_DATA_DIR=/tmp/fraud_data
export SPARK_MODELS_DIR=/tmp/fraud_models
export SPARK_CHECKPOINTS_DIR=/checkpoints
```

### Bước 3: Cài Dependencies

```bash
cd airflow_machine

# Setup virtual environment
bash setup_venv.sh

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Spark client (nếu chưa có)
bash install_spark_client.sh
```

### Bước 4: Verify Spark Connection

```bash
# Test Spark connection
spark-submit --master spark://$SPARK_IP:$SPARK_MASTER_PORT --version
```

Nếu lỗi, kiểm tra:
- Spark đã được cài trên Spark machine
- Network connectivity: `telnet $SPARK_IP $SPARK_MASTER_PORT`
- Firewall rules

### Bước 5: Start Airflow

```bash
cd airflow_machine

# Source environment variables (nếu dùng .env file)
source .env

# Start Airflow
bash start.sh
```

### Bước 6: Configure Airflow Connection

1. Mở Airflow UI: `http://airflow-machine-ip:8080`
2. Login: `admin/admin`
3. **Admin → Connections → Add/Edit:**
   - **Conn Id**: `spark_default`
   - **Conn Type**: `Spark`
   - **Host**: `<SPARK_IP>` (ví dụ: 192.168.1.134)
   - **Port**: `<SPARK_MASTER_PORT>` (ví dụ: 7077)
   - **Extra**: `{"master": "spark://<SPARK_IP>:<SPARK_MASTER_PORT>"}`

### Bước 7: Prepare Spark Machine

**Trên Spark Machine:**

```bash
cd spark_machine

# Tạo thư mục cho data và models
sudo mkdir -p /tmp/fraud_data
sudo mkdir -p /tmp/fraud_models
sudo mkdir -p /checkpoints

# Set permissions (cho phép tất cả users write)
sudo chmod 777 /tmp/fraud_data
sudo chmod 777 /tmp/fraud_models
sudo chmod 777 /checkpoints

# Copy training data (nếu chưa có)
# Copy train.csv vào /tmp/fraud_data/train.csv

# Start Spark cluster
bash start.sh
```

**Verify Spark:**
```bash
# Check Spark Master
jps | grep Master

# Check Spark Web UI
curl http://localhost:8080
```

### Bước 8: Prepare Kafka Machine

**Trên Kafka Machine:**

```bash
cd kafka_machine

# Start Kafka
bash start.sh

# Verify Kafka
docker ps | grep kafka
```

### Bước 9: Run Pipeline

1. Trong Airflow UI, tìm DAG `fraud_detection_pipeline`
2. Toggle ON để enable DAG
3. Click **"Trigger DAG"**
4. Monitor tasks trong Graph View

## 🔧 TROUBLESHOOTING

### Lỗi: "No such file or directory" khi submit Spark job

**Nguyên nhân:**
- Script không tồn tại tại path chỉ định
- Path không đúng trên máy mới

**Giải pháp:**
1. Chạy `verify_scripts` task để check
2. Verify paths trong DAG:
   ```python
   # Check trong Airflow UI → Task Logs
   # Hoặc chạy:
   python -c "from pathlib import Path; print(Path(__file__).parent)"
   ```
3. Đảm bảo environment variables được set đúng

### Lỗi: "Permission denied" trên Spark Worker

**Nguyên nhân:**
- Spark Worker không có quyền đọc file
- File owner không đúng

**Giải pháp:**
```bash
# Trên Spark machine
sudo chmod 755 /tmp/fraud_data
sudo chmod 755 /tmp/fraud_models
sudo chmod 755 /checkpoints

# Hoặc set owner
sudo chown -R spark:spark /tmp/fraud_data /tmp/fraud_models /checkpoints
```

### Lỗi: "ModuleNotFoundError: No module named 'spark_utils'"

**Nguyên nhân:**
- Dependencies không được upload cùng với main script

**Giải pháp:**
1. Verify `spark_utils.py` tồn tại trong `utils/` folder
2. Check DAG có sử dụng `files` parameter:
   ```python
   files=SPARK_UTILS_FILE if os.path.exists(SPARK_UTILS_FILE) else None,
   ```
3. Nếu vẫn lỗi, có thể cần đóng gói vào ZIP:
   ```bash
   cd airflow_machine
   zip -r scripts.zip scripts/ utils/
   ```

### Lỗi: "Connection refused" khi verify services

**Nguyên nhân:**
- Services chưa start
- IP addresses không đúng
- Firewall block ports

**Giải pháp:**
```bash
# Test connectivity
telnet $KAFKA_IP $KAFKA_PORT
telnet $SPARK_IP $SPARK_MASTER_PORT

# Check firewall
sudo ufw status
sudo ufw allow 9092/tcp
sudo ufw allow 7077/tcp
sudo ufw allow 8080/tcp
```

### Lỗi: "Data files not found"

**Nguyên nhân:**
- Data files không tồn tại tại path chỉ định
- Path không đúng

**Giải pháp:**
```bash
# Verify data files
ls -lh $FRAUD_DATA_DIR/stream.csv

# Hoặc check trong DAG
# Task verify_data_files sẽ show path đang check
```

## 📝 CHECKLIST DEPLOY

### Trước khi deploy:

- [ ] Clone repository trên tất cả 3 máy
- [ ] Chạy `setup_deployment.sh` trên Airflow machine
- [ ] Set environment variables hoặc source `.env` file
- [ ] Verify Spark installation trên Spark machine
- [ ] Verify Kafka installation trên Kafka machine
- [ ] Check network connectivity giữa các machines
- [ ] Verify data files tồn tại

### Sau khi deploy:

- [ ] Verify DAG visible trong Airflow UI
- [ ] Test Spark connection từ Airflow machine
- [ ] Run `verify_scripts` task thành công
- [ ] Run `verify_kafka_ready` task thành công
- [ ] Run `verify_spark_ready` task thành công
- [ ] Run `verify_data_files` task thành công
- [ ] Test submit một simple Spark job
- [ ] Run full pipeline

## 🎯 BEST PRACTICES

1. **Luôn sử dụng environment variables** cho IPs và paths
2. **Verify scripts tồn tại** trước khi submit job
3. **Set permissions đúng** trên Spark machine
4. **Test connectivity** trước khi chạy pipeline
5. **Monitor logs** trong Airflow UI để debug

## 📚 TÀI LIỆU THAM KHẢO

- [DEPLOYMENT_ANALYSIS.md](./DEPLOYMENT_ANALYSIS.md) - Phân tích chi tiết các vấn đề
- [README.md](./README.md) - Tài liệu chính của dự án
- [TESTING_GUIDE.md](./airflow_machine/TESTING_GUIDE.md) - Hướng dẫn testing

