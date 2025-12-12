"""
Airflow DAG: Fraud Detection Pipeline
Điều phối toàn bộ quy trình từ training đến streaming inference

LƯU Ý: Mỗi máy tự quản lý services của mình
- Kafka Machine: Tự start Kafka (không cần SSH)
- Spark Machine: Tự start Spark (không cần SSH)
- Airflow Machine: Chỉ submit jobs và chạy producer/viewer
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

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

# ========== TASK 1: VERIFY KAFKA READY ==========
# Giả định Kafka đã được start trên Kafka machine
# Có thể dùng Sensor để check Kafka ready
verify_kafka_ready = BashOperator(
    task_id='verify_kafka_ready',
    bash_command="""
        # Check Kafka accessible
        timeout 5 bash -c 'cat < /dev/null > /dev/tcp/kafka-machine-ip/9092' && echo "✓ Kafka is accessible" || (echo "✗ Kafka is not accessible" && exit 1)
    """,
    dag=dag,
)

# ========== TASK 2: VERIFY SPARK CLUSTER READY ==========
# Giả định Spark đã được start trên Spark machine
verify_spark_ready = BashOperator(
    task_id='verify_spark_ready',
    bash_command="""
        # Check Spark Master accessible
        timeout 5 bash -c 'cat < /dev/null > /dev/tcp/spark-machine-ip/7077' && echo "✓ Spark Master is accessible" || (echo "✗ Spark Master is not accessible" && exit 1)
        # Check Spark Web UI accessible
        curl -s http://spark-machine-ip:8080 > /dev/null && echo "✓ Spark Web UI is accessible" || (echo "✗ Spark Web UI is not accessible" && exit 1)
    """,
    dag=dag,
)

# ========== TASK 3: VERIFY DATA FILES ==========
verify_data_files = BashOperator(
    task_id='verify_data_files',
    bash_command="""
        # Try multiple possible locations
        DATA_DIR1="{{ dag.dag_folder }}/../data"
        DATA_DIR2="{{ dag.dag_folder }}/../../data"
        DATA_DIR3="{{ dag.dag_folder }}/data"
        
        if [ -f "$DATA_DIR1/train.csv" ] && [ -f "$DATA_DIR1/stream.csv" ]; then
            DATA_DIR="$DATA_DIR1"
        elif [ -f "$DATA_DIR2/train.csv" ] && [ -f "$DATA_DIR2/stream.csv" ]; then
            DATA_DIR="$DATA_DIR2"
        elif [ -f "$DATA_DIR3/train.csv" ] && [ -f "$DATA_DIR3/stream.csv" ]; then
            DATA_DIR="$DATA_DIR3"
        else
            echo "✗ Data files not found in any location"
            echo "Checked: $DATA_DIR1, $DATA_DIR2, $DATA_DIR3"
            exit 1
        fi
        
        echo "✓ Data files found in $DATA_DIR"
        ls -lh $DATA_DIR/*.csv
    """,
    dag=dag,
)

# ========== TASK 4: TRAIN MODEL ==========
train_model = SparkSubmitOperator(
    task_id='train_model',
    application='{{ dag.dag_folder }}/../scripts/train_model.py',
    conn_id='spark_default',  # Cần config trong Airflow Connections
    conf={
        'spark.master': 'spark://spark-machine-ip:7077',
    },
    application_args=[
        '--input', '{{ dag.dag_folder }}/../../data/train.csv',
        '--output', '/models/fraud_detection_v1',
    ],
    dag=dag,
)

# ========== TASK 5: START SPARK STREAMING ==========
start_spark_streaming = SparkSubmitOperator(
    task_id='start_spark_streaming',
    application='{{ dag.dag_folder }}/../scripts/streaming_inference.py',
    conn_id='spark_default',
    conf={
        'spark.master': 'spark://spark-machine-ip:7077',
    },
    application_args=[
        '--model-path', '/models/fraud_detection_v1',
        '--kafka-bootstrap', 'kafka-machine-ip:9092',
        '--input-topic', 'input_stream',
        '--output-topic', 'prediction_output',
    ],
    dag=dag,
)

# ========== TASK 6: VERIFY STREAMING RUNNING ==========
verify_streaming_running = BashOperator(
    task_id='verify_streaming_running',
    bash_command="""
        python3 {{ dag.dag_folder }}/../scripts/verify_streaming_job.py \
            --spark-ui-url http://spark-machine-ip:8080 \
            --job-name streaming \
            --timeout 600 \
            --check-interval 30
    """,
    dag=dag,
)

# ========== TASK 7: START PRODUCER ==========
start_producer = BashOperator(
    task_id='start_producer',
    bash_command="""
        # Find data file location
        if [ -f "{{ dag.dag_folder }}/../../data/stream.csv" ]; then
            DATA_FILE="{{ dag.dag_folder }}/../../data/stream.csv"
        elif [ -f "{{ dag.dag_folder }}/../data/stream.csv" ]; then
            DATA_FILE="{{ dag.dag_folder }}/../data/stream.csv"
        else
            echo "✗ stream.csv not found"
            exit 1
        fi
        
        python3 {{ dag.dag_folder }}/../scripts/producer.py \
            --input $DATA_FILE \
            --kafka-bootstrap kafka-machine-ip:9092 \
            --topic input_stream \
            --rate 10
    """,
    dag=dag,
)

# ========== TASK 8: START VIEWER ==========
start_viewer = BashOperator(
    task_id='start_viewer',
    bash_command="""
        streamlit run {{ dag.dag_folder }}/../scripts/viewer.py \
            --server.port 8501 \
            --server.address 0.0.0.0 &
        echo "Viewer started at http://$(hostname -I | awk '{print $1}'):8501"
    """,
    dag=dag,
)

# ========== DEPENDENCIES ==========
# Verify services ready trước khi chạy pipeline
verify_kafka_ready >> verify_spark_ready >> verify_data_files
verify_data_files >> train_model
train_model >> start_spark_streaming
start_spark_streaming >> verify_streaming_running
verify_streaming_running >> start_producer
start_producer >> start_viewer
