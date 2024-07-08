from confluent_kafka.admin import AdminClient, NewTopic, KafkaException
import time

def delete_topics(admin_client, topics):
    """Delete topics if they exist."""
    try:
        # List current topics
        metadata = admin_client.list_topics(timeout=10)
        existing_topics = set(metadata.topics.keys())
        # Filter out topics that don't exist
        topics_to_delete = [topic for topic in topics if topic in existing_topics]
        
        if topics_to_delete:
            # Perform deletion
            fs = admin_client.delete_topics(topics_to_delete, operation_timeout=30)
            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    print(f"Topic {topic} deleted successfully.")
                except KafkaException as e:
                    print(f"Failed to delete topic {topic}: {e}")
        else:
            print("No topics to delete.")
    except Exception as e:
        print(f"Error deleting topics: {e}")

def create_topics(admin_client, topics):
    """Create topics."""
    topic_list = [NewTopic(topic=topic, num_partitions=1, replication_factor=1) for topic in topics]
    try:
        fs = admin_client.create_topics(topic_list, validate_only=False)
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                print(f"Topic {topic} created successfully.")
            except KafkaException as e:
                if e.args[0].code() == KafkaException.TOPIC_ALREADY_EXISTS:
                    print(f"Topic {topic} already exists.")
                else:
                    print(f"Failed to create topic {topic}: {e}")
    except Exception as e:
        print(f"Error creating topics: {e}")

def ensure_topics(admin_client, topics):
    """Ensure topics exist by deleting and recreating them."""
    delete_topics(admin_client, topics)
    # Adding a short sleep to allow deletion to propagate
    time.sleep(2)
    create_topics(admin_client, topics)

def main():
    bootstrap_servers = 'localhost:9092'
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    
    topics = ['test_config', 'trigger_topic', 'metrics_topic', 'heartbeat_topic', 'register']

    ensure_topics(admin_client, topics)

if __name__ == "__main__":
    main()