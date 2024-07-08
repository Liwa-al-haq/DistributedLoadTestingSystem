from confluent_kafka import Consumer, Producer
import json
import requests
import time
import uuid
import sys
import threading

# Kafka configuration
kafka_consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': f'group_{sys.argv[1]}',
    'auto.offset.reset': 'latest'
})
kafka_producer = Producer({'bootstrap.servers': 'localhost:9092'})

# Kafka topics
test_config_topic = 'test_config'
trigger_topic = 'trigger_topic'
metrics_topic = 'metrics_topic'
heartbeat_topic = 'heartbeat_topic'
register_topic = 'register'

# Dictionary to store test configurations
tests = {}

class Driver:
    def __init__(self, node_id, node_ip):
        self.node_id = node_id
        self.node_ip = node_ip

    def publish_message(self, topic, message):
        kafka_producer.produce(topic, json.dumps(message).encode('utf-8'))
        kafka_producer.flush()

    def send_http_request(self):
        # Implement your HTTP request logic here
        response = requests.get('http://localhost:8080/ping')
        return response.elapsed.total_seconds() * 1000  # Convert to milliseconds

    def store_load_test(self, test_config):
        tests[test_config['test_id']] = test_config
        print(f"Stored test configuration: {test_config}")

    def run_load_test(self, test_config):
        test_id = test_config['test_id']
        if test_id not in tests:
            print(f"Test configuration not found for test_id: {test_id}")
            return
        
        print(f"Running load test: {test_id}")
        test = tests[test_id]
        message_count_per_driver = int(test['message_count_per_driver'])
        test_type = test['test_type']
        test_message_delay = int(test['test_message_delay'])
        time.sleep(0.5)
        latency_list = []

        for i in range(message_count_per_driver):
            latency = self.send_http_request()
            latency_list.append(latency)
            metrics_message = {
                'node_id': self.node_id,
                'test_id': test_id,
                'report_id': str(uuid.uuid4()),
                'metrics': {
                    'mean_latency': sum(latency_list) / len(latency_list),
                    'min_latency': min(latency_list),
                    'max_latency': max(latency_list),
                    'latency': latency
                }
            }
            self.publish_message(metrics_topic, metrics_message)

            if test_type == 'TSUNAMI' and test_message_delay > 0:
                time.sleep(test_message_delay / 1000.0)  # Convert to seconds

        # Signal end of metrics for the test
        kafka_producer.produce(metrics_topic, 'EOT'.encode('utf-8'))
        kafka_producer.flush()
        print(f"Load test {test_id} completed.")

    def heartbeat(self):
        while True:
            heartbeat_message = {
                'node_id': self.node_id,
                'heartbeat': 'YES'
            }
            self.publish_message(heartbeat_topic, heartbeat_message)
            time.sleep(1)

    def register(self):
        register_message = {
            'node_id': self.node_id,
            'node_ip': self.node_ip,
            'message_type': 'DRIVER_NODE_REGISTER'
        }
        self.publish_message(register_topic, register_message)
        print(f"Registered node {self.node_id} with IP {self.node_ip}.")

    def driver(self):
        # Subscribe to the test_config and trigger topics
        kafka_consumer.subscribe([test_config_topic, trigger_topic])

        while True:
            msg = kafka_consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue

            data = json.loads(msg.value().decode('utf-8'))
            print(f"Received message: {data}")

            if msg.topic() == test_config_topic:
                self.store_load_test(data)
            elif msg.topic() == trigger_topic:
                self.run_load_test(data)

if __name__ == '__main__':
    # Retrieve node_id and node_ip from command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python driver.py <node_id> <node_ip>")
        sys.exit(1)

    node_id = sys.argv[1]
    node_ip = sys.argv[2]

    # Initialize and start driver operations
    driver = Driver(node_id=node_id, node_ip=node_ip)
    driver.register()

    # Start driver and heartbeat in separate threads
    threading.Thread(target=driver.driver).start()
    threading.Thread(target=driver.heartbeat).start()