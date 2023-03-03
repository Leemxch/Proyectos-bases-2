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
ESINDEXFILES = os.getenv('ESINDEXFILES')
ESINDEXDAILY = os.getenv('ESINDEXDAILY')
# MariaDB env variables
MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')
# Extra
hostname = os.getenv('HOSTNAME')

def callback(ch, method, properties, body):
    print('Recibiendo msj de cola.')
    json_object = json.loads(body)
    fileName= json_object['data'][0]['msg']
    fileName.replace('.dly', '')
    parsed = getFile(fileName)
    elasticFiles(fileName, parsed)
    mariaFiles(fileName)
    # Send msg
    msg = "{\"data\": [ {\"msg\":\"" + fileName + "\", \"hostname\": \"" + hostname + "\"}]}"
    channel.basic_publish(exchange = '', routing_key = OUTPUT_QUEUE, body = msg)

def getFile(fileName):
    try:
        file = client.get(index = ESINDEXFILES, id=fileName)
        print(file['_source'])
        rawData = str(file['_source'])[2:]
        parse = rawData.split('\\n')
        temp = []
        for i in parse:
            fileContent = {
                'id': i[0:11],
                # month + year
                "date": i[15:17] + i[11:15],
                "element": i[17:21],
                "value": i[21:26],
                "mflag": i[26:27],
                "qflag": i[27:28],
                "sflag": i[28:29]
            }
            temp.append(fileContent)
        print(temp)
        return temp
    except:
        print("Archivo no encontrado: ", fileName)

def elasticFiles(fileName,parsed):
    doc = {
        "fileName": fileName,
        "data": parsed
    }
    try: # try to create the index ESINDEXDAILY
        client.indices.create(index=ESINDEXDAILY, mappings=doc)
    except: # ignore if exists
        pass
    # Remove the index of files and add the index daily in Elasticsearch
    client.index(index=ESINDEXDAILY, id= fileName, document= doc)
    try:
        client.delete(index=ESINDEXFILES, id= fileName)
    except:
        pass

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
                        SET file_state= 'PARSEADO'\
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

credentials_output = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_output = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_output)
connection_output = pika.BlockingConnection(parameters_output)
channel_output = connection_output.channel()
channel_output.queue_declare(queue=OUTPUT_QUEUE)

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)

print("Waiting...")
channel.start_consuming()