"""
Airflow DAG: Fraud Detection Pipeline
Điều phối toàn bộ quy trình từ training đến streaming inference

LƯU Ý: Mỗi máy tự quản lý services của mình
- Kafka Machine: Tự start Kafka (không cần SSH)
- Spark Machine: Tự start Spark (không cần SSH)
- Airflow Machine: Chỉ submit jobs và chạy producer/viewer

CẢI TIẾN: Sử dụng relative paths và environment variables để dễ deploy trên nhiều máy
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# ========== CONFIGURATION: Sử dụng Environment Variables hoặc Defaults ==========
# Lấy paths tương đối từ DAG folder
DAG_DIR = Path(__file__).parent.resolve()
AIRFLOW_MACHINE_DIR = DAG_DIR.parent.resolve()
PROJECT_ROOT = AIRFLOW_MACHINE_DIR.parent.resolve()

# Paths cho scripts và data (có thể override bằng environment variables)
SCRIPTS_DIR = Path(os.getenv("FRAUD_SCRIPTS_DIR", str(AIRFLOW_MACHINE_DIR / "scripts")))
UTILS_DIR = Path(os.getenv("FRAUD_UTILS_DIR", str(AIRFLOW_MACHINE_DIR / "utils")))
DATA_DIR = Path(os.getenv("FRAUD_DATA_DIR", str(PROJECT_ROOT / "data")))

# IP Addresses (có thể override bằng environment variables)
KAFKA_IP = os.getenv("KAFKA_IP", "192.168.1.3")
KAFKA_PORT = os.getenv("KAFKA_PORT", "9092")
SPARK_IP = os.getenv("SPARK_IP", "192.168.1.20")
SPARK_MASTER_PORT = os.getenv("SPARK_MASTER_PORT", "7077")
SPARK_WEB_UI_PORT = os.getenv("SPARK_WEB_UI_PORT", "8080")

# Spark paths trên Spark machine
SPARK_DATA_DIR = os.getenv("SPARK_DATA_DIR", "/tmp/fraud_data")
SPARK_MODELS_DIR = os.getenv("SPARK_MODELS_DIR", "/tmp/fraud_models")
SPARK_CHECKPOINTS_DIR = os.getenv("SPARK_CHECKPOINTS_DIR", "/checkpoints")

# Kafka topics
KAFKA_INPUT_TOPIC = os.getenv("KAFKA_INPUT_TOPIC", "input_stream")
KAFKA_OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC", "prediction_output")

# Script paths (absolute paths để đảm bảo SparkSubmitOperator tìm thấy)
TRAIN_MODEL_SCRIPT = str(SCRIPTS_DIR / "train_model.py")
STREAMING_SCRIPT = str(SCRIPTS_DIR / "streaming_inference.py")
VERIFY_STREAMING_SCRIPT = str(SCRIPTS_DIR / "verify_streaming_job.py")
PRODUCER_SCRIPT = str(SCRIPTS_DIR / "producer.py")
VIEWER_SCRIPT = str(SCRIPTS_DIR / "viewer.py")

# Utils file để upload cùng với scripts
SPARK_UTILS_FILE = str(UTILS_DIR / "spark_utils.py")

# Default arguments
default_args = {
    'owner': 'fraud_detection_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'fraud_detection_pipeline',
    default_args=default_args,
    description='End-to-end fraud detection pipeline with Spark ML and Kafka',
    schedule_interval=None,  # Manual trigger
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['fraud_detection', 'spark', 'kafka', 'ml'],
)

# ========== TASK 0: VERIFY SCRIPTS EXIST ==========
# Verify các scripts tồn tại trước khi submit
verify_scripts = BashOperator(
    task_id='verify_scripts',
    bash_command=f"""
        echo "Verifying scripts exist..."
        MISSING_FILES=0
        
        # Check train_model.py
        if [ ! -f "{TRAIN_MODEL_SCRIPT}" ]; then
            echo "✗ train_model.py not found at {TRAIN_MODEL_SCRIPT}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo "✓ train_model.py found"
        fi
        
        # Check streaming_inference.py
        if [ ! -f "{STREAMING_SCRIPT}" ]; then
            echo "✗ streaming_inference.py not found at {STREAMING_SCRIPT}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo "✓ streaming_inference.py found"
        fi
        
        # Check spark_utils.py
        if [ ! -f "{SPARK_UTILS_FILE}" ]; then
            echo "✗ spark_utils.py not found at {SPARK_UTILS_FILE}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo "✓ spark_utils.py found"
        fi
        
        # Check verify_streaming_job.py
        if [ ! -f "{VERIFY_STREAMING_SCRIPT}" ]; then
            echo "✗ verify_streaming_job.py not found at {VERIFY_STREAMING_SCRIPT}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo "✓ verify_streaming_job.py found"
        fi
        
        # Check producer.py
        if [ ! -f "{PRODUCER_SCRIPT}" ]; then
            echo "✗ producer.py not found at {PRODUCER_SCRIPT}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo "✓ producer.py found"
        fi
        
        # Check viewer.py
        if [ ! -f "{VIEWER_SCRIPT}" ]; then
            echo "✗ viewer.py not found at {VIEWER_SCRIPT}"
            MISSING_FILES=$((MISSING_FILES + 1))
        else
            echo "✓ viewer.py found"
        fi
        
        if [ $MISSING_FILES -gt 0 ]; then
            echo "✗ Total missing files: $MISSING_FILES"
            exit 1
        else
            echo "✓ All scripts found!"
        fi
    """,
    dag=dag,
)

# ========== TASK 1: VERIFY KAFKA READY ==========
# Giả định Kafka đã được start trên Kafka machine
# Có thể dùng Sensor để check Kafka ready
verify_kafka_ready = BashOperator(
    task_id='verify_kafka_ready',
    bash_command=f"""
        # Check Kafka accessible
        timeout 5 bash -c 'cat < /dev/null > /dev/tcp/{KAFKA_IP}/{KAFKA_PORT}' && echo "✓ Kafka is accessible at {KAFKA_IP}:{KAFKA_PORT}" || (echo "✗ Kafka is not accessible at {KAFKA_IP}:{KAFKA_PORT}" && exit 1)
    """,
    dag=dag,
)

# ========== TASK 2: VERIFY SPARK CLUSTER READY ==========
# Giả định Spark đã được start trên Spark machine
verify_spark_ready = BashOperator(
    task_id='verify_spark_ready',
    bash_command=f"""
        # Check Spark Master accessible
        timeout 5 bash -c 'cat < /dev/null > /dev/tcp/{SPARK_IP}/{SPARK_MASTER_PORT}' && echo "✓ Spark Master is accessible at {SPARK_IP}:{SPARK_MASTER_PORT}" || (echo "✗ Spark Master is not accessible at {SPARK_IP}:{SPARK_MASTER_PORT}" && exit 1)
        # Check Spark Web UI accessible
        curl -s http://{SPARK_IP}:{SPARK_WEB_UI_PORT} > /dev/null && echo "✓ Spark Web UI is accessible at http://{SPARK_IP}:{SPARK_WEB_UI_PORT}" || (echo "✗ Spark Web UI is not accessible at http://{SPARK_IP}:{SPARK_WEB_UI_PORT}" && exit 1)
    """,
    dag=dag,
)

# ========== TASK 3: VERIFY DATA FILES ==========
# NOTE: This task checks files on Airflow machine (for producer)
# Training data is on Spark machine at SPARK_DATA_DIR
verify_data_files = BashOperator(
    task_id='verify_data_files',
    bash_command=f"""
        # Use path from environment variable or default
        DATA_DIR="{DATA_DIR}"
        
        echo "Checking data files in: $DATA_DIR"
        echo "Current working directory: $(pwd)"
        
        # Check if stream.csv exists (needed for producer on Airflow machine)
        if [ -f "$DATA_DIR/stream.csv" ]; then
            echo "✓ stream.csv found in $DATA_DIR (for producer)"
            ls -lh "$DATA_DIR/stream.csv"
        else
            echo "✗ stream.csv not found in $DATA_DIR"
            echo "Checking if directory exists:"
            ls -la "$DATA_DIR" 2>&1 || echo "Directory does not exist"
            exit 1
        fi
        echo "NOTE: train.csv should be on Spark machine at {SPARK_DATA_DIR}/train.csv"
    """,
    dag=dag,
)

# ========== TASK 4: TRAIN MODEL ==========
# Note: SparkSubmitOperator sẽ tự động upload application file lên Spark cluster
# Các file dependencies có thể được upload qua 'files' parameter nếu cần
train_model = SparkSubmitOperator(
    task_id='train_model',
    # Application file on Airflow machine (will be uploaded to Spark cluster)
    application=TRAIN_MODEL_SCRIPT,
    conn_id='spark_default',  # Cần config trong Airflow Connections
    # Upload additional files nếu cần (Spark sẽ tự động thêm vào PYTHONPATH)
    files=SPARK_UTILS_FILE if os.path.exists(SPARK_UTILS_FILE) else None,
    conf={
        'spark.master': f'spark://{SPARK_IP}:{SPARK_MASTER_PORT}',
        'spark.hadoop.fs.defaultFS': 'file:///',  # Use local filesystem instead of HDFS
        'spark.hadoop.fs.file.impl': 'org.apache.hadoop.fs.LocalFileSystem',
    },
    application_args=[
        '--input', f'{SPARK_DATA_DIR}/train.csv',
        '--output', f'{SPARK_MODELS_DIR}/fraud_detection_v1',
    ],
    dag=dag,
)

# ========== TASK 5: START SPARK STREAMING ==========
# Note: SparkSubmitOperator sẽ tự động upload application file lên Spark cluster
start_spark_streaming = SparkSubmitOperator(
    task_id='start_spark_streaming',
    # Application file on Airflow machine (will be uploaded to Spark cluster)
    application=STREAMING_SCRIPT,
    conn_id='spark_default',
    # Upload additional files nếu cần
    files=SPARK_UTILS_FILE if os.path.exists(SPARK_UTILS_FILE) else None,
    conf={
        'spark.master': f'spark://{SPARK_IP}:{SPARK_MASTER_PORT}',
        'spark.hadoop.fs.defaultFS': 'file:///',  # Use local filesystem instead of HDFS
        'spark.hadoop.fs.file.impl': 'org.apache.hadoop.fs.LocalFileSystem',
    },
    application_args=[
        '--model-path', f'file://{SPARK_MODELS_DIR}/fraud_detection_v1',
        '--kafka-bootstrap', f'{KAFKA_IP}:{KAFKA_PORT}',
        '--input-topic', KAFKA_INPUT_TOPIC,
        '--output-topic', KAFKA_OUTPUT_TOPIC,
        '--checkpoint-location', f'{SPARK_CHECKPOINTS_DIR}/streaming_inference',
    ],
    dag=dag,
)

# ========== TASK 6: VERIFY STREAMING RUNNING ==========
verify_streaming_running = BashOperator(
    task_id='verify_streaming_running',
    bash_command=f"""
        # Add utils to Python path
        export PYTHONPATH="{UTILS_DIR}:$PYTHONPATH"
        python3 "{VERIFY_STREAMING_SCRIPT}" \
            --spark-ui-url http://{SPARK_IP}:{SPARK_WEB_UI_PORT} \
            --job-name streaming \
            --timeout 600 \
            --check-interval 30
    """,
    dag=dag,
)

# ========== TASK 7: START PRODUCER ==========
start_producer = BashOperator(
    task_id='start_producer',
    bash_command=f"""
        # Find data file location
        DATA_FILE="{DATA_DIR}/stream.csv"
        if [ ! -f "$DATA_FILE" ]; then
            echo "✗ stream.csv not found at $DATA_FILE"
            exit 1
        fi
        
        python3 "{PRODUCER_SCRIPT}" \
            --input "$DATA_FILE" \
            --kafka-bootstrap {KAFKA_IP}:{KAFKA_PORT} \
            --topic {KAFKA_INPUT_TOPIC} \
            --rate 10
    """,
    dag=dag,
)

# ========== TASK 8: START VIEWER ==========
start_viewer = BashOperator(
    task_id='start_viewer',
    bash_command=f"""
        streamlit run "{VIEWER_SCRIPT}" \
            --server.port 8501 \
            --server.address 0.0.0.0 &
        echo "Viewer started at http://$(hostname -I | awk '{{print $1}}'):8501"
    """,
    dag=dag,
)

# ========== DEPENDENCIES ==========
# Verify scripts và services ready trước khi chạy pipeline
verify_scripts >> verify_kafka_ready >> verify_spark_ready >> verify_data_files
verify_data_files >> train_model
train_model >> start_spark_streaming
start_spark_streaming >> verify_streaming_running
verify_streaming_running >> start_producer
start_producer >> start_viewer
