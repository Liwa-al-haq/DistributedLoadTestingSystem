from flask import Flask, jsonify
from kafka import KafkaProducer
from kafka import KafkaConsumer
import json
import uuid
import time
app = Flask(__name__)
producer = KafkaProducer(bootstrap_servers='localhost:9092')
consumer = KafkaConsumer('metrics_topic13', bootstrap_servers='localhost:9092', auto_offset_reset='earliest')

def generate_test_config(test_type, test_message_delay, message_count_per_driver):
    test_id = str(uuid.uuid4())  
    test_config = {
        'test_id': test_id,
        'test_type': test_type,
        'test_message_delay': test_message_delay,
        'message_count_per_driver': message_count_per_driver,
    }
    return test_id, test_config


@app.route('/start_avalanche_test', methods=['GET'])
def start_avalanche_test():
    test_id, test_config = generate_test_config('AVALANCHE', 0, 100)
    producer.send('test_config', json.dumps(test_config).encode('utf-8'))
    
    # Send the trigger message to start the test
    trigger_message = {
        'test_id': test_id,
        'trigger': 'YES'
    }
    producer.send('trigger_topic', json.dumps(trigger_message).encode('utf-8'))
    
    return "Avalanche Test Started", 200
@app.route('/start_tsunami_test', methods=['GET'])
def start_tsunami_test():
    test_id, test_config = generate_test_config('TSUNAMI', 1, 100)
    producer.send('test_config', json.dumps(test_config).encode('utf-8'))
    
    # Send the trigger message to start the test
    trigger_message = {
        'test_id': test_id,
        'trigger': 'YES'
    }
    producer.send('trigger_topic', json.dumps(trigger_message).encode('utf-8'))
    
    return "Tsunami Test Started", 200


@app.route('/metrics', methods=['GET'])
def get_metrics():
    all_metrics = []
    records = consumer.poll(timeout_ms=1000)
    for topic_partition, messages in records.items():
        for message in messages:
            all_metrics.append(json.loads(message.value.decode()))

    return jsonify(all_metrics)

orchestrator_node_id = str(uuid.uuid4()) 

@app.route('/heartbeat', methods=['GET'])
def get_heartbeat_status():
    heartbeat_status = {
        'node_id': orchestrator_node_id,  
        'heartbeat': 'YES',
        'timestamp': str(time.time())
    }
    producer.send('heartbeat_topic4', json.dumps(heartbeat_status).encode('utf-8'))
    
    return jsonify(heartbeat_status)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
