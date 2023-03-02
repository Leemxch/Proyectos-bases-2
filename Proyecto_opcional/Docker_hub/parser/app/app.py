import os
import re
import pika
import json
import mariadb
from elasticsearch import Elasticsearch

# Rabbit MQ env variables
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITPASS')
# Elasticsearch env variables
OUTPUT_QUEUE=os.getenv('OUTPUT_QUEUE')
INPUT_QUEUE=os.getenv('INPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
# MariaDB env variables
MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')

def callback(ch, method, properties, body):
    name = body["fileName"]
    parsed = getFiles(body)
    msg = {
        "fileName": name,
        "data": parsed
    }

    # Remove the index of files and add the index daily in Elasticsearch
    #client.indices.create(index="daily", id= name, document= msg)
    #client.indices.delete(index="files", doc = name)

    # Update the table weather.files
    try:
        connection.execute("UPDATE files \
                        SET file_state= 'PARSEADO'\
                        WHERE file_name = ?", (name,))
    except:
        print("No se ha encontrado el archivo")

    # Send msg
    channel.basic_publish(exchange = '', routing_key = OUTPUT_QUEUE, body = json.dump(msg))

def getFiles(body):
    contents = body["contents"]
    files = contents.split("\\n")
    temp = []
    for i in files:
        try:
            file = {
                'id': i[1:11],
                "year": i[12:15],
                "month": i[16:17],
                "element": i[18:21],
                "value": i[22:26],
                "mflag": i[27:27],
                "qflag": i[28:28],
                "sflag": i[29:29]
            }
            print(file)
            temp.append(file)
        except:
            print("Something went wrong")
            pass
    return temp

credentials_input = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_input = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_input)
connection_input = pika.BlockingConnection(parameters_input)
channel = connection_input.channel()
channel.queue_declare(queue=INPUT_QUEUE)
channel.basic_consume(queue=INPUT_QUEUE, on_message_callback=callback, auto_ack=True) 

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)

# Mariadb connection
mariaDatabase = mariadb.connect(
    host=MARIAHOST,
    port=int(MARIAPORT),
    user=MARIAUSER, 
    password=MARIAPASS,
    database=MARIADB
)
connection = mariaDatabase.cursor()

print("Waiting...")
channel.start_consuming()