# PHÂN TÍCH HỆ THỐNG VÀ CÁC VẤN ĐỀ KHI DEPLOY

## 🔍 TỔNG QUAN VẤN ĐỀ

Khi deploy hệ thống lên các máy khác, gặp lỗi: **Spark Worker không thể truy cập file Python scripts** (`train_model.py`, `streaming_inference.py`).

## 📋 PHÂN TÍCH CHI TIẾT CÁC VẤN ĐỀ

### 1. ❌ HARDCODED PATHS (Đường dẫn cứng)

**Vấn đề:**
- DAG sử dụng đường dẫn tuyệt đối: `/home/phanvantai/Documents/four_years/bigdata/the_end/...`
- Chỉ đúng trên máy hiện tại
- Khi deploy lên máy khác, user khác, path khác → **LỖI**

**Vị trí:**
```python
# airflow_machine/dags/fraud_detection_pipeline.py
application='/home/phanvantai/Documents/four_years/bigdata/the_end/airflow_machine/scripts/train_model.py'
```

**Ảnh hưởng:**
- SparkSubmitOperator không tìm thấy file
- Airflow không thể submit job

---

### 2. ❌ SPARK WORKER PERMISSIONS (Quyền truy cập)

**Vấn đề:**
- SparkSubmitOperator upload file từ Airflow machine lên Spark cluster
- File được upload vào thư mục tạm của Spark (thường là `/tmp/spark-*`)
- Spark Worker chạy dưới user khác (có thể là `spark` user hoặc user khác)
- Worker không có quyền truy cập vào:
  - Home directory của user Airflow
  - Thư mục tạm nếu permissions không đúng

**Cơ chế hoạt động:**
1. Airflow (user: `phanvantai`) chạy `spark-submit`
2. Spark Master nhận job và phân phát cho Worker
3. Worker (user: `spark` hoặc user khác) cần truy cập file
4. **LỖI**: Permission denied hoặc File not found

---

### 3. ❌ PYTHON DEPENDENCIES (Phụ thuộc Python)

**Vấn đề:**
- Script `verify_streaming_job.py` import từ `utils/spark_utils.py`:
  ```python
  from spark_utils import verify_spark_job_running
  ```
- Khi SparkSubmitOperator upload file, nó chỉ upload file chính
- **KHÔNG upload** các file dependencies trong `utils/`
- Spark Worker không tìm thấy module `spark_utils`

**Vị trí:**
```python
# airflow_machine/scripts/verify_streaming_job.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from spark_utils import verify_spark_job_running
```

**Ảnh hưởng:**
- ImportError khi chạy script
- Job fail ngay khi start

---

### 4. ❌ SPARK INSTALLATION PATH (Đường dẫn cài đặt Spark)

**Vấn đề:**
- Script giả định Spark ở `/opt/spark`
- Trên các máy khác có thể:
  - Spark ở vị trí khác (`/usr/local/spark`, `~/spark`, etc.)
  - Không có Spark installed
  - SPARK_HOME không được set

**Vị trí:**
```bash
# spark_machine/start_spark_cluster.sh
SPARK_HOME=${SPARK_HOME:-/opt/spark}
```

**Ảnh hưởng:**
- Không start được Spark cluster
- SparkSubmitOperator không tìm thấy `spark-submit`

---

### 5. ❌ DATA FILE PATHS (Đường dẫn file dữ liệu)

**Vấn đề:**
- Training data: `/tmp/fraud_data/train.csv` (trên Spark machine)
- Stream data: `/home/phanvantai/.../data/stream.csv` (trên Airflow machine)
- Hardcoded paths không flexible

**Vị trí:**
```python
# DAG
application_args=[
    '--input', '/tmp/fraud_data/train.csv',
    '--output', '/tmp/fraud_models/fraud_detection_v1',
]

# verify_data_files task
DATA_DIR="/home/phanvantai/Documents/four_years/bigdata/the_end/data"
```

**Ảnh hưởng:**
- File không tồn tại trên máy khác
- Job fail khi không tìm thấy data

---

### 6. ❌ NETWORK CONFIGURATION (Cấu hình mạng)

**Vấn đề:**
- IP addresses hardcoded: `192.168.1.60`, `192.168.1.134`
- Không tự động detect IP
- Không có cơ chế fallback

**Vị trí:**
```python
# DAG
'timeout 5 bash -c \'cat < /dev/null > /dev/tcp/192.168.1.60/9092\''
'spark.master': 'spark://192.168.1.134:7077'
```

**Ảnh hưởng:**
- Không connect được đến services
- Verify tasks fail

---

### 7. ❌ FILE UPLOAD MECHANISM (Cơ chế upload file)

**Vấn đề:**
- SparkSubmitOperator upload file qua network
- File được copy vào thư mục tạm trên Spark Master
- Spark Master phân phát file cho Workers
- **NHƯNG**: Nếu file lớn hoặc network chậm → timeout
- Nếu permissions không đúng → Worker không đọc được

**Cơ chế:**
```
Airflow Machine (file: train_model.py)
    ↓ (upload via spark-submit)
Spark Master (/tmp/spark-xxx/train_model.py)
    ↓ (distribute to workers)
Spark Workers (/tmp/spark-xxx/train_model.py)
```

**Vấn đề tiềm ẩn:**
- File upload timeout
- Worker không có quyền đọc
- File bị corrupt trong quá trình transfer

---

## ✅ GIẢI PHÁP ĐỀ XUẤT

### Giải pháp 1: Sử dụng Relative Paths + Environment Variables

**Thay đổi:**
- Sử dụng `{{ dag.folder }}` hoặc `os.path.dirname(__file__)` để lấy path tương đối
- Sử dụng environment variables cho các paths quan trọng

**Code:**
```python
import os
from pathlib import Path

# Lấy path tương đối từ DAG folder
DAG_DIR = Path(__file__).parent
SCRIPTS_DIR = DAG_DIR.parent / "scripts"
DATA_DIR = os.getenv("FRAUD_DATA_DIR", str(DAG_DIR.parent.parent / "data"))

application=str(SCRIPTS_DIR / "train_model.py")
```

---

### Giải pháp 2: Copy Files vào Shared Location trên Spark Machine

**Thay đổi:**
- Trước khi submit job, copy files vào thư mục shared trên Spark machine
- Sử dụng thư mục có quyền truy cập công khai: `/tmp/spark_scripts/` hoặc `/opt/spark_scripts/`

**Code:**
```python
# Task mới: prepare_scripts
prepare_scripts = BashOperator(
    task_id='prepare_scripts',
    bash_command=f"""
        # Copy scripts lên Spark machine
        scp {SCRIPTS_DIR}/*.py spark-machine:/tmp/spark_scripts/
        # Hoặc dùng rsync qua SSH
    """,
)
```

**Vấn đề:** Cần SSH setup giữa Airflow và Spark machines

---

### Giải pháp 3: Sử dụng PyFiles để Upload Dependencies

**Thay đổi:**
- Sử dụng `py_files` parameter của SparkSubmitOperator để upload các file dependencies
- Đóng gói utils vào một package

**Code:**
```python
train_model = SparkSubmitOperator(
    task_id='train_model',
    application=str(SCRIPTS_DIR / "train_model.py"),
    py_files=[
        str(DAG_DIR.parent / "utils" / "spark_utils.py"),
    ],
    # ...
)
```

---

### Giải pháp 4: Sử dụng Spark Archives (ZIP)

**Thay đổi:**
- Đóng gói toàn bộ scripts và dependencies vào một ZIP file
- Upload ZIP file lên Spark cluster
- Spark tự động extract và thêm vào PYTHONPATH

**Code:**
```python
# Tạo ZIP file chứa scripts và utils
# Trong DAG:
train_model = SparkSubmitOperator(
    task_id='train_model',
    application=str(SCRIPTS_DIR / "train_model.py"),
    archives=[str(SCRIPTS_DIR.parent / "scripts_archive.zip")],
    # ...
)
```

---

### Giải pháp 5: Sử dụng Shared Filesystem (NFS/S3)

**Thay đổi:**
- Mount shared filesystem (NFS) trên cả 3 máy
- Lưu scripts và data trên shared filesystem
- Tất cả machines truy cập cùng một path

**Ví dụ:**
```
/shared/fraud_detection/
├── scripts/
│   ├── train_model.py
│   └── streaming_inference.py
├── data/
│   ├── train.csv
│   └── stream.csv
└── models/
```

**Code:**
```python
SHARED_DIR = "/shared/fraud_detection"
application=f"{SHARED_DIR}/scripts/train_model.py"
```

---

### Giải pháp 6: Sử dụng Docker để Đảm bảo Consistency

**Thay đổi:**
- Đóng gói scripts vào Docker image
- Spark Workers chạy trong Docker containers
- Đảm bảo môi trường giống nhau trên tất cả machines

**Vấn đề:** Phức tạp hơn, cần setup Docker trên Spark cluster

---

## 🎯 GIẢI PHÁP ĐƯỢC KHUYẾN NGHỊ

### Kết hợp Giải pháp 1 + 3 + 4:

1. **Relative Paths**: Sử dụng relative paths thay vì hardcoded
2. **PyFiles**: Upload dependencies qua `py_files`
3. **Environment Variables**: Sử dụng env vars cho IPs và paths
4. **Validation**: Thêm tasks để verify files tồn tại trước khi submit

### Implementation Plan:

1. ✅ Sửa DAG để sử dụng relative paths
2. ✅ Thêm `py_files` cho SparkSubmitOperator
3. ✅ Tạo task để verify scripts tồn tại
4. ✅ Sử dụng environment variables cho IPs
5. ✅ Tạo script setup để copy files vào shared location (optional)

---

## 📝 CHECKLIST KHI DEPLOY

### Trước khi deploy:

- [ ] Kiểm tra Spark installation path trên Spark machine
- [ ] Kiểm tra SPARK_HOME được set đúng
- [ ] Kiểm tra permissions trên Spark machine (`/tmp`, `/opt/spark_scripts`)
- [ ] Kiểm tra network connectivity giữa các machines
- [ ] Kiểm tra Python version trên Spark Workers (phải >= 3.8)
- [ ] Kiểm tra PySpark được cài trên Spark Workers

### Sau khi deploy:

- [ ] Test SparkSubmitOperator với simple job
- [ ] Verify files được upload đúng
- [ ] Check Spark Worker logs để xem có lỗi permissions không
- [ ] Test với actual scripts (train_model.py, streaming_inference.py)

---

## 🔧 TROUBLESHOOTING

### Lỗi: "No such file or directory"

**Nguyên nhân:**
- File không tồn tại tại path chỉ định
- Path không đúng trên máy khác

**Giải pháp:**
- Sử dụng relative paths
- Verify file tồn tại trước khi submit

### Lỗi: "Permission denied"

**Nguyên nhân:**
- Spark Worker không có quyền đọc file
- File owner không đúng

**Giải pháp:**
- Copy file vào thư mục có quyền công khai (`/tmp/spark_scripts/`)
- Set permissions: `chmod 755 /tmp/spark_scripts/*.py`

### Lỗi: "ModuleNotFoundError: No module named 'spark_utils'"

**Nguyên nhân:**
- Dependencies không được upload cùng với main script

**Giải pháp:**
- Sử dụng `py_files` parameter
- Hoặc đóng gói vào ZIP file

---

## 📚 TÀI LIỆU THAM KHẢO

- [SparkSubmitOperator Documentation](https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/stable/operators/spark-submit.html)
- [Spark Application Submission](https://spark.apache.org/docs/latest/submitting-applications.html)
- [Spark Python Dependencies](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)

