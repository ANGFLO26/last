#!/usr/bin/env python3
"""
Streamlit Viewer App
Đọc kết quả prediction từ Kafka và hiển thị real-time visualization
"""
import os
import streamlit as st
import pandas as pd
import json
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go


# Page config
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 Fraud Detection Real-time Dashboard")
st.markdown("---")

# Sidebar configuration
st.sidebar.header("Configuration")
kafka_bootstrap = st.sidebar.text_input(
    "Kafka Bootstrap Servers",
    value=os.getenv("KAFKA_BOOTSTRAP", "192.168.1.3:9092"),
    help="Kafka bootstrap servers (host:port)"
)
topic = st.sidebar.text_input(
    "Topic",
    value="prediction_output",
    help="Kafka topic to consume from"
)
refresh_interval = st.sidebar.slider(
    "Refresh Interval (seconds)",
    min_value=1,
    max_value=60,
    value=5,
    help="How often to refresh the dashboard"
)
max_records = st.sidebar.slider(
    "Max Records to Display",
    min_value=10,
    max_value=1000,
    value=100,
    help="Maximum number of records to display"
)

# Initialize session state
if 'predictions' not in st.session_state:
    st.session_state.predictions = []
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total': 0,
        'fraud': 0,
        'normal': 0,
        'fraud_rate': 0.0
    }


@st.cache_resource
def create_consumer(bootstrap_servers, topic_name):
    """Create Kafka consumer"""
    try:
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fraud_detection_viewer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        return consumer
    except Exception as e:
        st.error(f"Error creating Kafka consumer: {e}")
        return None


def parse_prediction(message):
    """Parse prediction message from Kafka"""
    try:
        value = message.value
        return {
            'transaction_id': value.get('transaction_id', 'N/A'),
            'timestamp': value.get('timestamp', 'N/A'),
            'prediction': value.get('prediction', -1),
            'probability': value.get('probability', 'N/A'),
            'model_version': value.get('model_version', 'N/A'),
            'prediction_timestamp': value.get('prediction_timestamp', 'N/A')
        }
    except Exception as e:
        st.error(f"Error parsing message: {e}")
        return None


def update_stats(predictions):
    """Update statistics"""
    if not predictions:
        return
    
    total = len(predictions)
    fraud = sum(1 for p in predictions if p.get('prediction') == 1)
    normal = total - fraud
    fraud_rate = (fraud / total * 100) if total > 0 else 0.0
    
    st.session_state.stats = {
        'total': total,
        'fraud': fraud,
        'normal': normal,
        'fraud_rate': fraud_rate
    }


# Main content
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Predictions", st.session_state.stats['total'])
with col2:
    st.metric("Fraud Detected", st.session_state.stats['fraud'], delta=None)
with col3:
    st.metric("Normal Transactions", st.session_state.stats['normal'], delta=None)
with col4:
    st.metric("Fraud Rate", f"{st.session_state.stats['fraud_rate']:.2f}%")

st.markdown("---")

# Create consumer
consumer = create_consumer(kafka_bootstrap, topic)

if consumer:
    # Placeholder for real-time updates
    placeholder = st.empty()
    
    # Button to start/stop consuming
    if st.button("Start Consuming", key="start_btn"):
        st.info("Consuming messages from Kafka...")
        
        # Consume messages
        try:
            messages_consumed = 0
            for message in consumer:
                prediction = parse_prediction(message)
                if prediction:
                    st.session_state.predictions.append(prediction)
                    messages_consumed += 1
                    
                    # Keep only last max_records
                    if len(st.session_state.predictions) > max_records:
                        st.session_state.predictions = st.session_state.predictions[-max_records:]
                    
                    # Update stats
                    update_stats(st.session_state.predictions)
                    
                    # Display every refresh_interval messages
                    if messages_consumed % refresh_interval == 0:
                        with placeholder.container():
                            # Display recent predictions
                            if st.session_state.predictions:
                                df = pd.DataFrame(st.session_state.predictions[-20:])  # Last 20
                                
                                # Charts
                                col_chart1, col_chart2 = st.columns(2)
                                
                                with col_chart1:
                                    # Fraud vs Normal pie chart
                                    fraud_count = st.session_state.stats['fraud']
                                    normal_count = st.session_state.stats['normal']
                                    
                                    fig_pie = px.pie(
                                        values=[normal_count, fraud_count],
                                        names=['Normal', 'Fraud'],
                                        title="Transaction Distribution",
                                        color_discrete_map={'Normal': 'green', 'Fraud': 'red'}
                                    )
                                    st.plotly_chart(fig_pie, use_container_width=True)
                                
                                with col_chart2:
                                    # Timeline chart
                                    if len(st.session_state.predictions) > 1:
                                        df_timeline = pd.DataFrame(st.session_state.predictions)
                                        df_timeline['prediction'] = df_timeline['prediction'].astype(str)
                                        
                                        fig_timeline = px.scatter(
                                            df_timeline.tail(50),
                                            x='prediction_timestamp',
                                            y='prediction',
                                            color='prediction',
                                            title="Recent Predictions Timeline",
                                            labels={'prediction': 'Prediction (0=Normal, 1=Fraud)'}
                                        )
                                        st.plotly_chart(fig_timeline, use_container_width=True)
                                
                                # Recent predictions table
                                st.subheader("Recent Predictions")
                                st.dataframe(df, use_container_width=True)
                                
                                # Statistics
                                st.subheader("Statistics")
                                st.json(st.session_state.stats)
        except KeyboardInterrupt:
            st.warning("Stopped consuming messages")
        except Exception as e:
            st.error(f"Error consuming messages: {e}")
    
    # Display current predictions
    if st.session_state.predictions:
        st.subheader("All Predictions")
        df_all = pd.DataFrame(st.session_state.predictions)
        st.dataframe(df_all, use_container_width=True)
        
        # Download button
        csv = df_all.to_csv(index=False)
        st.download_button(
            label="Download Predictions CSV",
            data=csv,
            file_name=f"fraud_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
else:
    st.error("Failed to create Kafka consumer. Please check configuration.")

# Footer
st.markdown("---")
st.markdown("**Note**: Make sure Kafka is running and topic exists before starting consumption.")

