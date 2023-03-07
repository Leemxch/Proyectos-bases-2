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
INPUT_QUEUE=os.getenv('INPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
ESINDEXWEATHER = os.getenv('ESINDEXWEATHER')
ESINDEXDAILY = os.getenv('ESINDEXDAILY')
# MariaDB env variables
MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')

def callback(ch, method, properties, body):
    print('Recibiendo msj de cola.')
    json_object = json.loads(body)
    fileName= json_object['data'][0]['msg']
    data = getFile(fileName)
    elasticFiles(fileName, data)
    mariaFiles(fileName)
    print("Archivo procesado: ", fileName)

def getFile(fileName):
    try:
        file = client.get(index = ESINDEXDAILY, id=fileName)
        print(file['_source']["contents"])
        latitude = file['_source']["latitude"]
        longitude = file['_source']["longitude"]
        temp = [latitude, longitude]
        print(temp)
        return temp
    except:
        print("Archivo no encontrado: ", fileName)
        return []

def elasticFiles(fileName,map):
    doc = {
        "fileName": fileName,
        "latitude": map[0],
        "longitude": map[1]
    }
    try: # try to create the index ESINDEXWEATHER
        client.indices.create(index=ESINDEXWEATHER, mappings=doc)
    except: # ignore if exists
        pass
    # Remove the index daily in Elasticsearch
    client.delete(index=ESINDEXDAILY, id= fileName)

def mariaFiles(fileName):
    # Mariadb connection
    mariaDatabase = mariadb.connect(
        host=MARIAHOST,
        port=int(MARIAPORT),
        user=MARIAUSER, 
        password=MARIAPASS,
        database=MARIADB
    )
    connection = mariaDatabase.cursor()
    # Update the table weather.files
    try:
        connection.execute("UPDATE files \
                        SET file_state= 'PROCESADO'\
                        WHERE file_name = ?", (fileName,))
    except:
        print("No se ha encontrado el archivo")
    # Close connection
    mariaDatabase.commit()
    mariaDatabase.close()

credentials_input = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_input = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_input)
connection_input = pika.BlockingConnection(parameters_input)
channel = connection_input.channel()
channel.queue_declare(queue=INPUT_QUEUE)
channel.basic_consume(queue=INPUT_QUEUE, on_message_callback=callback, auto_ack=True) 

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)

print("Waiting...")
channel.start_consuming()