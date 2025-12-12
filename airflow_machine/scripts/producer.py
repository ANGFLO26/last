#!/usr/bin/env python3
"""
Kafka Producer Script
Đọc stream.csv và gửi messages vào Kafka topic input_stream
"""
import argparse
import csv
import json
import time
import sys
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime


def create_producer(kafka_bootstrap):
    """Create Kafka producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1,
            enable_idempotence=True
        )
        print(f"Kafka producer created: {kafka_bootstrap}")
        return producer
    except Exception as e:
        print(f"Error creating producer: {e}", file=sys.stderr)
        raise


def read_csv_file(file_path):
    """Read CSV file and return records"""
    records = []
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        print(f"Read {len(records)} records from {file_path}")
        return records
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        raise


def convert_record_to_json(record):
    """Convert CSV record to JSON format"""
    # Convert numeric fields
    json_record = {}
    for key, value in record.items():
        if key in ['Time', 'Amount'] or key.startswith('V'):
            try:
                json_record[key] = float(value) if value else 0.0
            except ValueError:
                json_record[key] = 0.0
        elif key == 'Class':
            try:
                json_record[key] = int(value) if value else 0
            except ValueError:
                json_record[key] = 0
        elif key == 'transaction_id':
            json_record[key] = value
        elif key == 'timestamp':
            json_record[key] = value
        else:
            json_record[key] = value
    
    return json_record


def send_messages(producer, records, topic, rate=10):
    """Send messages to Kafka at specified rate"""
    print(f"Sending {len(records)} messages to topic '{topic}' at rate {rate} messages/second...")
    
    interval = 1.0 / rate  # Time between messages in seconds
    sent_count = 0
    failed_count = 0
    
    try:
        for i, record in enumerate(records):
            # Convert record to JSON
            json_record = convert_record_to_json(record)
            
            # Use transaction_id as key (if available)
            key = json_record.get('transaction_id', f'txn_{i:08d}')
            
            # Send message
            future = producer.send(topic, key=key, value=json_record)
            
            # Wait for result (optional, for error checking)
            try:
                record_metadata = future.get(timeout=10)
                sent_count += 1
                
                if (sent_count + failed_count) % 100 == 0:
                    print(f"Sent {sent_count} messages, failed {failed_count} messages...")
            except KafkaError as e:
                failed_count += 1
                print(f"Error sending message {i}: {e}", file=sys.stderr)
            
            # Rate limiting
            if i < len(records) - 1:  # Don't sleep after last message
                time.sleep(interval)
        
        # Flush remaining messages
        producer.flush()
        
        print("\n" + "="*50)
        print(f"Finished sending messages!")
        print(f"Total sent: {sent_count}")
        print(f"Total failed: {failed_count}")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Flushing remaining messages...")
        producer.flush()
        print(f"Sent {sent_count} messages before interruption")
    except Exception as e:
        print(f"Error sending messages: {e}", file=sys.stderr)
        producer.flush()
        raise


def main():
    parser = argparse.ArgumentParser(description='Kafka Producer - Send CSV data to Kafka')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--kafka-bootstrap', required=True, help='Kafka bootstrap servers (host:port)')
    parser.add_argument('--topic', default='input_stream', help='Kafka topic name')
    parser.add_argument('--rate', type=int, default=10, help='Messages per second')
    parser.add_argument('--loop', action='store_true', help='Loop through data continuously')
    
    args = parser.parse_args()
    
    try:
        # Create producer
        producer = create_producer(args.kafka_bootstrap)
        
        # Read CSV
        records = read_csv_file(args.input)
        
        if not records:
            print("No records to send!", file=sys.stderr)
            sys.exit(1)
        
        # Send messages
        if args.loop:
            print("Looping mode: will send data continuously...")
            while True:
                send_messages(producer, records, args.topic, args.rate)
                print("\nRestarting from beginning...")
                time.sleep(1)
        else:
            send_messages(producer, records, args.topic, args.rate)
        
    except KeyboardInterrupt:
        print("\nProducer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

