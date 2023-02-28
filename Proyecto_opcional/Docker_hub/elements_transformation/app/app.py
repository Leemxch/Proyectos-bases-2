import os
import pika
import json
from elasticsearch import Elasticsearch


def callback(ch, method, properties, body):
    message = json.loads(body)
    
    


# Environment variables
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD = os.getenv('RABBITPASS')
INPUT_QUEUE = os.getenv('INPUT_QUEUE')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
ESINDEXDAILY = os.getenv('ESINDEXDAILY')

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)

# RabbitMQ connection
credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters = pika.ConnectionParameters(host = RABBIT_MQ, credentials = credentials, heartbeat = 600)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue = INPUT_QUEUE)
channel.queue_declare(queue = OUTPUT_QUEUE)
channel.basic_consume(queue = INPUT_QUEUE, on_message_callback = callback, auto_ack = True)
print('Esperando mensaje del parser')
channel.start_consuming()

