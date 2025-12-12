#!/usr/bin/env python3
"""
Script để verify Spark streaming job đã RUNNING
Dùng cho Airflow task verify_streaming_running
"""
import sys
import os

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

from spark_utils import verify_spark_job_running

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Spark streaming job is running')
    parser.add_argument('--spark-ui-url', required=True, help='Spark Web UI URL')
    parser.add_argument('--job-name', default='streaming', help='Job name pattern')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout in seconds')
    parser.add_argument('--check-interval', type=int, default=30, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    try:
        result = verify_spark_job_running(
            spark_ui_url=args.spark_ui_url,
            job_name=args.job_name,
            timeout=args.timeout,
            check_interval=args.check_interval
        )
        
        if result:
            print("✓ Spark streaming job is RUNNING")
            sys.exit(0)
        else:
            print("✗ Spark streaming job is NOT RUNNING")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

