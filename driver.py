import requests
import json
import time
import socket
import sys
import random
import uuid
import logging
from statistics import mean, median
from kafka import KafkaConsumer,KafkaProducer
KAFKA_SERVERS = 'localhost:9092'
TEST_TOPIC = 'test4'
METRICS_TOPIC = 'metrics_topic13'
REGISTER_TOPIC = 'register'
HEARTBEAT_TOPIC = 'heartbeat_topic4'
driver_id = sys.argv[1] if len(sys.argv) > 1 else 'default_driver_id'
driver_port = '3001'

producer = KafkaProducer(bootstrap_servers=KAFKA_SERVERS)
consumer = KafkaConsumer(TEST_TOPIC, bootstrap_servers=KAFKA_SERVERS, auto_offset_reset='earliest')

logging.basicConfig(level=logging.INFO)

def register_driver_node(driver_id, driver_port):
    node_ip = socket.gethostbyname(socket.gethostname())
    node_ip_with_port = f'{node_ip}:{driver_port}'
    register_message = {
        'node_id': driver_id,
        'node_IP': node_ip_with_port,
        'message_type': 'DRIVER_NODE_REGISTER'
    }
    producer.send(REGISTER_TOPIC, json.dumps(register_message).encode('utf-8'))
    logging.info(f"Driver node registered: {register_message}")

def calculate_metrics(response_times):
    if not response_times:
        return {
            "mean_latency": 0,
            "median_latency": 0,
            "min_latency": 0,
            "max_latency": 0,
        }

    mean_latency = mean(response_times)
    median_latency = median(response_times)
    min_latency = min(response_times)
    max_latency = max(response_times)

    return {
        "mean_latency": mean_latency,
        "median_latency": median_latency,
        "min_latency": min_latency,
        "max_latency": max_latency,
    }

def send_request(target_url, response_times):
    try:
        response = requests.get(target_url)
        response_time = response.elapsed.total_seconds()
        response_times.append(response_time)

        metrics = {
            'node_id': driver_id,
            'test_id': str(uuid.uuid4()),  
            'report_id': str(uuid.uuid4()),  
            'metrics': calculate_metrics(response_times), 
        }
        producer.send(METRICS_TOPIC, json.dumps(metrics).encode('utf-8'))
        logging.info(f"Metrics sent: {metrics}")

        max_latency = max(response_times)
        logging.info(f"Max Latency: {max_latency} seconds")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending request: {e}")

def run_test(test_type, target_url, delay_interval=1):
    logging.info(f"Running test {test_type}")
    response_times = []  # List to store response times for metrics calculation
    if test_type == 'TSUNAMI':
        while True:
            send_request(target_url, response_times)
            time.sleep(delay_interval)
    elif test_type == 'AVALANCHE':
        while True:
            send_request(target_url, response_times)
def send_heartbeat(driver_id):
    heartbeat_message = {
        'node_id': driver_id,
        'heartbeat': 'YES',
        'timestamp': str(time.time())
    }
    producer.send(HEARTBEAT_TOPIC, json.dumps(heartbeat_message).encode('utf-8'))
    logging.info(f"Sending heartbeat: {heartbeat_message}")


def listen_for_test_configurations():
    for message in consumer:
        try:
            test_config = json.loads(message.value.decode())
            logging.info(f"Received test configuration: {test_config}")
            test_type = test_config.get('test_type')
            if test_type:
                
                run_test(test_type, target_url=test_config.get('target_url'))
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding message: {e}")

if __name__ == '__main__':
    register_driver_node(driver_id, driver_port)
    test_id = str(uuid.uuid4())
    listen_for_test_configurations()
    while True:
        send_heartbeat(driver_id)
        time.sleep(60)
