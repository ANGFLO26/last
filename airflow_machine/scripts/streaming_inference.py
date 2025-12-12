#!/usr/bin/env python3
"""
Spark Structured Streaming Inference Script
Đọc từ Kafka, predict với trained model, ghi kết quả về Kafka
"""
import argparse
import sys
import json
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.functions import col, from_json, struct, to_json, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType


def create_spark_session(app_name="FraudDetectionStreaming"):
    """Create Spark session for streaming"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.streaming.checkpointLocation", "/checkpoints/streaming_inference") \
        .getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    return spark


def get_input_schema():
    """Define schema for input Kafka messages"""
    schema = StructType([
        StructField("Time", DoubleType(), True),
        StructField("V1", DoubleType(), True),
        StructField("V2", DoubleType(), True),
        StructField("V3", DoubleType(), True),
        StructField("V4", DoubleType(), True),
        StructField("V5", DoubleType(), True),
        StructField("V6", DoubleType(), True),
        StructField("V7", DoubleType(), True),
        StructField("V8", DoubleType(), True),
        StructField("V9", DoubleType(), True),
        StructField("V10", DoubleType(), True),
        StructField("V11", DoubleType(), True),
        StructField("V12", DoubleType(), True),
        StructField("V13", DoubleType(), True),
        StructField("V14", DoubleType(), True),
        StructField("V15", DoubleType(), True),
        StructField("V16", DoubleType(), True),
        StructField("V17", DoubleType(), True),
        StructField("V18", DoubleType(), True),
        StructField("V19", DoubleType(), True),
        StructField("V20", DoubleType(), True),
        StructField("V21", DoubleType(), True),
        StructField("V22", DoubleType(), True),
        StructField("V23", DoubleType(), True),
        StructField("V24", DoubleType(), True),
        StructField("V25", DoubleType(), True),
        StructField("V26", DoubleType(), True),
        StructField("V27", DoubleType(), True),
        StructField("V28", DoubleType(), True),
        StructField("Amount", DoubleType(), True),
        StructField("Class", IntegerType(), True),
        StructField("transaction_id", StringType(), True),
        StructField("timestamp", StringType(), True),
    ])
    return schema


def load_model(model_path):
    """Load trained model"""
    print(f"Loading model from {model_path}...")
    try:
        model = PipelineModel.load(model_path)
        print("Model loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        raise


def read_from_kafka(spark, kafka_bootstrap, input_topic):
    """Read stream from Kafka"""
    print(f"Reading from Kafka topic: {input_topic}")
    
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap) \
        .option("subscribe", input_topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    return df


def parse_kafka_messages(df, schema):
    """Parse JSON messages from Kafka"""
    # Extract value and convert from binary to string
    df = df.select(
        col("key").cast("string").alias("key"),
        col("value").cast("string").alias("value"),
        col("timestamp").alias("kafka_timestamp"),
        col("partition"),
        col("offset")
    )
    
    # Parse JSON
    df = df.withColumn("data", from_json(col("value"), schema))
    
    # Extract fields
    df = df.select(
        col("data.*"),
        col("kafka_timestamp"),
        col("partition"),
        col("offset")
    )
    
    return df


def prepare_features(df):
    """Prepare features for model prediction"""
    # Select feature columns (same as training)
    feature_cols = [f"V{i}" for i in range(1, 29)] + ["Amount", "Time"]
    
    # Handle null values
    for col_name in feature_cols:
        df = df.withColumn(col_name, col(col_name).cast("double"))
        df = df.withColumn(col_name, col(col_name).fillna(0.0))
    
    return df


def make_predictions(model, df):
    """Make predictions using loaded model"""
    print("Making predictions...")
    
    # Transform data
    predictions = model.transform(df)
    
    return predictions


def format_output(predictions):
    """Format predictions for Kafka output"""
    # Extract probability array
    predictions = predictions.withColumn(
        "probability_array",
        col("probability").cast("string")
    )
    
    # Create output schema
    output_df = predictions.select(
        col("transaction_id").alias("transaction_id"),
        col("timestamp").alias("timestamp"),
        col("prediction").cast("integer").alias("prediction"),
        col("probability_array").alias("probability"),
        lit("v1").alias("model_version"),
        current_timestamp().alias("prediction_timestamp")
    )
    
    # Convert to JSON
    output_df = output_df.select(
        to_json(struct([
            col("transaction_id"),
            col("timestamp"),
            col("prediction"),
            col("probability"),
            col("model_version"),
            col("prediction_timestamp")
        ])).alias("value")
    )
    
    return output_df


def write_to_kafka(df, kafka_bootstrap, output_topic):
    """Write predictions to Kafka"""
    print(f"Writing to Kafka topic: {output_topic}")
    
    query = df \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap) \
        .option("topic", output_topic) \
        .option("checkpointLocation", "/checkpoints/streaming_inference") \
        .outputMode("append") \
        .start()
    
    return query


def main():
    parser = argparse.ArgumentParser(description='Spark Streaming Inference')
    parser.add_argument('--model-path', required=True, help='Path to trained model')
    parser.add_argument('--kafka-bootstrap', required=True, help='Kafka bootstrap servers')
    parser.add_argument('--input-topic', default='input_stream', help='Input Kafka topic')
    parser.add_argument('--output-topic', default='prediction_output', help='Output Kafka topic')
    parser.add_argument('--checkpoint-location', default='/checkpoints/streaming_inference',
                       help='Checkpoint location')
    
    args = parser.parse_args()
    
    # Create Spark session
    spark = create_spark_session("FraudDetectionStreaming")
    
    try:
        # Load model
        model = load_model(args.model_path)
        
        # Read from Kafka
        kafka_df = read_from_kafka(spark, args.kafka_bootstrap, args.input_topic)
        
        # Parse messages
        input_schema = get_input_schema()
        parsed_df = parse_kafka_messages(kafka_df, input_schema)
        
        # Prepare features
        features_df = prepare_features(parsed_df)
        
        # Make predictions
        predictions_df = make_predictions(model, features_df)
        
        # Format output
        output_df = format_output(predictions_df)
        
        # Write to Kafka
        query = write_to_kafka(output_df, args.kafka_bootstrap, args.output_topic)
        
        print("\n" + "="*50)
        print("Streaming inference started!")
        print(f"Reading from: {args.input_topic}")
        print(f"Writing to: {args.output_topic}")
        print("="*50)
        print("\nWaiting for data... (Press Ctrl+C to stop)")
        
        # Wait for termination
        query.awaitTermination()
        
    except KeyboardInterrupt:
        print("\nStopping streaming...")
        query.stop()
        print("Streaming stopped!")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

