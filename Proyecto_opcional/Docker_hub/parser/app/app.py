import os
import pika
import json
from elasticsearch import Elasticsearch

# Env variables
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITPASS')
OUTPUT_QUEUE=os.getenv('OUTPUT_QUEUE')
INPUT_QUEUE=os.getenv('INPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
ESINDEXGROUPS = os.getenv('ESINDEXGROUPS')

def callback(ch, method, properties, body):
    print("Should generate a JSON from de .dly")

credentials_input = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_input = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_input)
connection_input = pika.BlockingConnection(parameters_input)
channel_input = connection_input.channel()
channel_input.queue_declare(queue=INPUT_QUEUE)
channel_input.basic_consume(queue=INPUT_QUEUE, on_message_callback=callback, auto_ack=True) 

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)

'''
credentials_output = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_output = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_output)
connection_output = pika.BlockingConnection(parameters_output)
channel_output = connection_output.channel()
channel_output.queue_declare(queue=OUTPUT_QUEUE)
'''

channel_input.start_consuming()
