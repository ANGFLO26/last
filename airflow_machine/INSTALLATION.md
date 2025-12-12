# Airflow Installation Guide

## Vấn đề xung đột dependency

Khi cài đặt Apache Airflow 2.7.0 trong môi trường global, bạn có thể gặp xung đột với các thư viện khác:

- **pydantic**: Airflow 2.7.0 yêu cầu pydantic 1.10.24, nhưng các thư viện như albumentations, langchain, llama-index cần pydantic >= 2.7.4
- **protobuf**: Airflow yêu cầu protobuf 4.25.8, nhưng TensorFlow cần protobuf >= 5.28.0
- **starlette**: Airflow yêu cầu starlette 0.50.0, nhưng FastAPI cần starlette < 0.28.0

## Giải pháp: Sử dụng Virtual Environment

Cách tốt nhất để tránh xung đột là sử dụng virtual environment riêng cho Airflow.

### Cách 1: Sử dụng script tự động (Khuyến nghị)

```bash
cd airflow_machine
bash setup_venv.sh
source venv/bin/activate
```

### Cách 2: Tạo thủ công

```bash
cd airflow_machine

# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
source venv/bin/activate

# Cài đặt requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Sử dụng Virtual Environment

Mỗi khi làm việc với Airflow:

```bash
# Kích hoạt
cd airflow_machine
source venv/bin/activate

# Chạy Airflow commands
airflow db init
airflow webserver
airflow scheduler

# Tắt virtual environment khi xong
deactivate
```

## Giải pháp thay thế: Nâng cấp Airflow

Nếu bạn muốn sử dụng pydantic 2.x, bạn có thể thử nâng cấp lên Airflow 2.8.0 hoặc mới hơn (nếu có), nhưng cần kiểm tra tương thích.

## Kiểm tra cài đặt

Sau khi cài đặt, kiểm tra:

```bash
source venv/bin/activate
airflow version
python -c "import airflow; print(airflow.__version__)"
```

## Lưu ý

- Luôn kích hoạt virtual environment trước khi chạy Airflow
- Nếu bạn cần sử dụng cả Airflow và các thư viện khác (như TensorFlow, LangChain), hãy tạo các virtual environment riêng biệt
- Có thể sử dụng `conda` hoặc `poetry` thay vì `venv` nếu bạn quen thuộc hơn
