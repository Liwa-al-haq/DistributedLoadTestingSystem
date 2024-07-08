from flask import Flask, request, jsonify, render_template, redirect, url_for
from confluent_kafka import Producer, Consumer, KafkaException
import json
import uuid
import threading
import time
from turbo_flask import Turbo
import logging

app = Flask(__name__)
turbo = Turbo(app)

# Enable logging
logging.basicConfig(level=logging.INFO)

# Kafka configuration
kafka_producer = Producer({'bootstrap.servers': 'localhost:9092'})
kafka_consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'orchestrator-group',
    'auto.offset.reset': 'latest'
})

# Kafka topics
test_config_topic = 'test_config'
trigger_topic = 'trigger_topic'
metrics_topic = 'metrics_topic'
heartbeat_topic = 'heartbeat_topic'
register_topic = 'register'

# Store test details and node registrations
test_details = {}
registered_nodes = []
driver_last_heartbeat = {}
driver_metrics = {}

class Orchestrator:
    def publish_message(self, topic, message):
        kafka_producer.produce(topic, json.dumps(message).encode('utf-8'))
        kafka_producer.flush()

    def consume_metrics(self):
        kafka_consumer.subscribe([metrics_topic])
        with app.app_context():
            while True:
                msg = kafka_consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logging.error(f"Consumer error: {msg.error()}")
                    continue
                if msg.value().decode() == 'EOT':
                    logging.info("Received EOT message")
                    break
                data = json.loads(msg.value().decode('utf-8'))
                logging.info(f"Received metrics: {data}")
                driver_id = data['node_id']
                metrics = data['metrics']
                driver_metrics[driver_id] = metrics  # Update driver_metrics
                turbo.push(turbo.replace(render_template('results.html', test_details=test_details, nodes=driver_metrics, driver_last_heartbeat=driver_last_heartbeat, current_time=time.time()), 'load'))
            logging.info('Test Over')

    def heartbeat(self):
        kafka_consumer2 = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'orchestrator-group1',
            'auto.offset.reset': 'latest'
        })
        kafka_consumer2.subscribe([heartbeat_topic])
        with app.app_context():
            while True:
                msg = kafka_consumer2.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logging.error("Consumer error: {}".format(msg.error()))
                    continue
                try:
                    data = json.loads(msg.value().decode('utf-8'))
                    driver_id = data['node_id']
                    driver_last_heartbeat[driver_id] = time.time()
                    logging.info(f"Received heartbeat from driver {driver_id}")
                    turbo.push(turbo.replace(render_template('results.html', test_details=test_details, nodes=driver_metrics, driver_last_heartbeat=driver_last_heartbeat, current_time=time.time()), 'load'))
                    logging.info("Pushed update to Turbo-Flask")
                except json.JSONDecodeError:
                    logging.error("Failed to decode JSON message")
                except KeyError:
                    logging.error("Missing expected key in message")

    def handle_load_test(self, config):
        self.publish_message(test_config_topic, config)
        test_details[config['test_id']] = config
        return redirect(url_for('results'))

    def trigger_load_test(self, trigger_message):
        self.publish_message(trigger_topic, trigger_message)
        threading.Thread(target=self.consume_metrics).start()
        return redirect(url_for('results'))

    def get_driver_status(self):
        current_time = time.time()
        status = {}
        for driver_id, last_heartbeat_time in driver_last_heartbeat.items():
            time_since_last_heartbeat = current_time - last_heartbeat_time
            status[driver_id] = {'last_heartbeat_time': last_heartbeat_time,
                                 'status': 'alive' if time_since_last_heartbeat < 5 else 'dead'}
        return jsonify({'driver_status': status})

    def register_nodes(self):
        kafka_consumer1 = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'orchestrator-group2',
            'auto.offset.reset': 'latest'
        })
        kafka_consumer1.subscribe([register_topic])
        while True:
            msg = kafka_consumer1.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logging.error("Consumer error: {}".format(msg.error()))
                continue
            data = json.loads(msg.value().decode('utf-8'))
            registered_nodes.append(data['node_id'])

orchestrator_instance = Orchestrator()

@app.route('/', methods=['GET', 'POST'])
def load_test():
    if request.method == 'POST':
        test_id = str(uuid.uuid4())
        test_type = request.form['test_type']
        test_config = {
            "query": "create_test",
            "test_id": test_id,
            "test_type": test_type,
            "test_message_delay": request.form['test_message_delay'],
            "message_count_per_driver": request.form['message_count_per_driver']
        }
        return orchestrator_instance.handle_load_test(test_config)
    return render_template('Home.html', test_details=test_details)

@app.route('/trigger/<test_id>', methods=['POST'])
def trigger_test(test_id):
    trigger_message = {
        "query": "trigger_test",
        "test_id": test_id,
        "trigger": "YES"
    }
    return orchestrator_instance.trigger_load_test(trigger_message)

@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify({'metrics': driver_metrics})

@app.route('/status', methods=['GET'])
def get_status():
    return orchestrator_instance.get_driver_status()

@app.route('/register', methods=['POST'])
def register_node():
    node_info = request.get_json()
    driver_last_heartbeat[node_info['node_id']] = time.time()
    return jsonify({'message': 'Node registered successfully'})

@app.route('/results', methods=['GET'])
def results():
    return render_template('results.html', test_details=test_details, nodes=driver_metrics, driver_last_heartbeat=driver_last_heartbeat, current_time=time.time())

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

if __name__ == '__main__':
    # Start heartbeat and node registration in separate threads
    threading.Thread(target=orchestrator_instance.heartbeat).start()
    threading.Thread(target=orchestrator_instance.register_nodes).start()

    # Start the Flask app in the main thread with a different port
    app.run(port=8012, debug=True)
