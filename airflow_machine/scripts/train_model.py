#!/usr/bin/env python3
"""
Spark ML Training Script
Huấn luyện model Fraud Detection từ train.csv
"""
import argparse
import sys
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql.functions import col, when, isnan, isnull


def create_spark_session(app_name="FraudDetectionTraining"):
    """Create Spark session"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    return spark


def load_data(spark, input_path):
    """Load training data from CSV"""
    print(f"Loading data from {input_path}...")
    df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(input_path)
    
    print(f"Data loaded: {df.count()} rows, {len(df.columns)} columns")
    return df


def preprocess_data(df):
    """Preprocess data: handle missing values, select features"""
    print("Preprocessing data...")
    
    # Select feature columns (V1-V28, Amount, Time)
    feature_cols = [f"V{i}" for i in range(1, 29)] + ["Amount", "Time"]
    
    # Handle missing values
    for col_name in feature_cols + ["Class"]:
        df = df.withColumn(
            col_name,
            when(isnan(col(col_name)) | isnull(col(col_name)), 0.0)
            .otherwise(col(col_name))
        )
    
    # Ensure Class is integer
    df = df.withColumn("Class", col("Class").cast("integer"))
    
    # Select only needed columns
    df = df.select(feature_cols + ["Class"])
    
    print(f"After preprocessing: {df.count()} rows")
    
    # Show class distribution
    print("\nClass distribution:")
    df.groupBy("Class").count().show()
    
    return df, feature_cols


def create_pipeline(feature_cols, model_type="random_forest"):
    """Create ML pipeline"""
    print(f"Creating {model_type} pipeline...")
    
    # Vector Assembler: combine features into single vector
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    
    # Standard Scaler: normalize features
    scaler = StandardScaler(
        inputCol="features",
        outputCol="scaledFeatures",
        withMean=True,
        withStd=True
    )
    
    # Model
    if model_type == "random_forest":
        model = RandomForestClassifier(
            featuresCol="scaledFeatures",
            labelCol="Class",
            numTrees=100,
            maxDepth=10,
            seed=42
        )
    elif model_type == "gbt":
        model = GBTClassifier(
            featuresCol="scaledFeatures",
            labelCol="Class",
            maxIter=100,
            maxDepth=10,
            seed=42
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Create pipeline
    pipeline = Pipeline(stages=[assembler, scaler, model])
    
    return pipeline


def train_model(pipeline, train_df, validation_df=None):
    """Train model"""
    print("Training model...")
    
    # Fit pipeline
    model = pipeline.fit(train_df)
    
    print("Model training completed!")
    
    return model


def evaluate_model(model, test_df):
    """Evaluate model"""
    print("Evaluating model...")
    
    # Make predictions
    predictions = model.transform(test_df)
    
    # Binary Classification Evaluator (AUC)
    binary_evaluator = BinaryClassificationEvaluator(
        labelCol="Class",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC"
    )
    auc = binary_evaluator.evaluate(predictions)
    print(f"AUC: {auc:.4f}")
    
    # Multiclass Classification Evaluator
    multiclass_evaluator = MulticlassClassificationEvaluator(
        labelCol="Class",
        predictionCol="prediction",
        metricName="accuracy"
    )
    accuracy = multiclass_evaluator.evaluate(predictions)
    print(f"Accuracy: {accuracy:.4f}")
    
    # Precision, Recall, F1
    precision = multiclass_evaluator.setMetricName("weightedPrecision").evaluate(predictions)
    recall = multiclass_evaluator.setMetricName("weightedRecall").evaluate(predictions)
    f1 = multiclass_evaluator.setMetricName("f1").evaluate(predictions)
    
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    
    # Confusion Matrix
    print("\nConfusion Matrix:")
    predictions.groupBy("Class", "prediction").count().orderBy("Class", "prediction").show()
    
    return {
        "auc": auc,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


def save_model(model, output_path):
    """Save trained model"""
    print(f"Saving model to {output_path}...")
    model.write().overwrite().save(output_path)
    print(f"Model saved successfully!")


def save_metrics(metrics, output_path):
    """Save training metrics to file"""
    import json
    metrics_path = f"{output_path}/metrics.json"
    print(f"Saving metrics to {metrics_path}...")
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("Metrics saved!")


def main():
    parser = argparse.ArgumentParser(description='Train Fraud Detection Model')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output model path')
    parser.add_argument('--model-type', default='random_forest', choices=['random_forest', 'gbt'],
                       help='Model type: random_forest or gbt')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                       help='Train/validation split ratio')
    
    args = parser.parse_args()
    
    # Create Spark session
    spark = create_spark_session("FraudDetectionTraining")
    
    try:
        # Load data
        df = load_data(spark, args.input)
        
        # Preprocess
        df, feature_cols = preprocess_data(df)
        
        # Split data
        train_df, test_df = df.randomSplit([args.train_ratio, 1 - args.train_ratio], seed=42)
        print(f"\nTrain set: {train_df.count()} rows")
        print(f"Test set: {test_df.count()} rows")
        
        # Create pipeline
        pipeline = create_pipeline(feature_cols, args.model_type)
        
        # Train model
        model = train_model(pipeline, train_df)
        
        # Evaluate
        metrics = evaluate_model(model, test_df)
        
        # Save model
        save_model(model, args.output)
        
        # Save metrics
        save_metrics(metrics, args.output)
        
        print("\n" + "="*50)
        print("Training completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

