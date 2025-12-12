"""
Utility functions for Spark operations
"""
import requests
import time
from typing import Optional, Dict


def verify_spark_job_running(
    spark_ui_url: str,
    job_name: str = "streaming",
    timeout: int = 600,
    check_interval: int = 30
) -> bool:
    """
    Verify Spark streaming job is running
    
    Args:
        spark_ui_url: Spark Web UI URL (e.g., "http://192.168.1.134:8080")
        job_name: Name pattern to search for in job names
        timeout: Maximum time to wait in seconds
        check_interval: Interval between checks in seconds
    
    Returns:
        True if job is RUNNING, False otherwise
    """
    api_url = f"{spark_ui_url}/api/v1/applications"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                apps = response.json()
                
                # Find streaming job
                streaming_job = None
                for app in apps:
                    if job_name.lower() in app.get('name', '').lower():
                        streaming_job = app
                        break
                
                if streaming_job:
                    state = streaming_job.get('state', '').upper()
                    if state == 'RUNNING':
                        return True
                    elif state in ['FAILED', 'FINISHED', 'KILLED']:
                        raise Exception(f"Spark job is in {state} state")
                
            time.sleep(check_interval)
        except requests.exceptions.RequestException as e:
            print(f"Error checking Spark job: {e}")
            time.sleep(check_interval)
    
    raise Exception(f"Spark streaming job did not start within {timeout} seconds")


def get_spark_job_info(spark_ui_url: str, job_name: str = "streaming") -> Optional[Dict]:
    """
    Get information about Spark job
    
    Args:
        spark_ui_url: Spark Web UI URL
        job_name: Name pattern to search for
    
    Returns:
        Job info dict or None if not found
    """
    api_url = f"{spark_ui_url}/api/v1/applications"
    
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            apps = response.json()
            for app in apps:
                if job_name.lower() in app.get('name', '').lower():
                    return app
    except requests.exceptions.RequestException as e:
        print(f"Error getting Spark job info: {e}")
    
    return None

