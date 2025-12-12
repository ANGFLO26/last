# CÀI ĐẶT SPARK CLIENT TRÊN AIRFLOW MACHINE

## 🔍 Vấn đề

**SparkSubmitOperator** cần `spark-submit` command có sẵn trên máy Airflow để submit jobs đến Spark cluster.

Hiện tại:
- ✅ `spark_machine`: Có Spark installed (version 3.5.0)
- ❌ `airflow_machine`: Không có Spark installed

## ✅ Giải pháp: Cài Spark Client trên Airflow Machine

### Bước 1: Download Spark

```bash
# Trên airflow_machine
cd ~/Documents
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xzf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark
```

### Bước 2: Set Environment Variables

```bash
# Thêm vào ~/.bashrc hoặc ~/.profile
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# Reload
source ~/.bashrc
```

### Bước 3: Verify Installation

```bash
# Kiểm tra spark-submit
spark-submit --version

# Kiểm tra có thể connect đến Spark cluster
spark-submit --master spark://192.168.1.134:7077 --version
```

### Bước 4: Update Airflow Connection (nếu cần)

Trong Airflow UI:
- Admin → Connections → Edit `spark_default`
- Extra field:
  ```json
  {"master": "spark://192.168.1.134:7077"}
  ```

## 📝 Lưu ý

1. **Chỉ cần Spark Client**: Không cần start Spark Master/Worker trên Airflow machine
2. **SPARK_HOME**: Phải được set để SparkSubmitOperator tìm thấy
3. **Network**: Đảm bảo Airflow machine có thể connect đến Spark Master (192.168.1.134:7077)

## 🔧 Alternative: Dùng BashOperator

Nếu không muốn cài Spark trên Airflow machine, có thể dùng BashOperator để SSH vào Spark machine và chạy spark-submit từ đó. Nhưng cách này cần SSH setup.

## ✅ Sau khi cài

Sau khi cài Spark client, SparkSubmitOperator sẽ hoạt động và có thể submit jobs đến Spark cluster.

