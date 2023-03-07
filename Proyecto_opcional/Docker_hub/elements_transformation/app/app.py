import os
import pika
import json
from elasticsearch import Elasticsearch
import mariadb
from mariadb import Error


def callback(ch, method, properties, body):
    message = json.loads(body)
    print("Message received: ")
    print(message)
    fileName = message['data'][0]['msg']
    nameFile = fileName[0:len(fileName)]
    dataFile = client.get(index = ESINDEXDAILY, id = nameFile)
    # si existe
    if dataFile['found']:
        print("found file in Elasticsearch")
        dicFile = dataFile['_source']
        dicDataList = dicFile['data']
        print("adding values")
        for i in range(0, len(dicDataList)):
            station_id = dicDataList[i]['id']
            if len(station_id) < 11:
                continue
            # agrega mes y año
            dicDataList[i]['month'] = dicDataList[i]['date'][0:2]
            dicDataList[i]['year'] = dicDataList[i]['date'][2:6]
            # agrega valores del station_id
            dicDataList[i]['FIPS_country_code'] = station_id[0:2]
            dicDataList[i]['network_code'] = station_id[2]
            dicDataList[i]['real_station_id'] = station_id[3:len(station_id)]
            # agrega nombre del tipo
            tipo = dicDataList[i]['element']
            if tipo == "PRCP":
                dicDataList[i]['type_name'] = "Precipitation (tenths of mm)"
            elif tipo == "SNOW":
                dicDataList[i]['type_name'] = "Snowfall (mm)"
            elif tipo == "SNWD":
                dicDataList[i]['type_name'] = "Snow depth (mm)"
            elif tipo == "TMAX":
                dicDataList[i]['type_name'] = "Maximum temperature (tenths of degrees C)"
            elif tipo == "TMIN":
                dicDataList[i]['type_name'] = "Minimum temperature (tenths of degrees C)"
            elif tipo == "RHMX":
                dicDataList[i]['type_name'] = "Maximum relative humidity for the day (percent)"
            else:
                dicDataList[i]['type_name'] = ""
        dicFile['data'] = dicDataList
        # Actualiza datos en Elasticsearch
        print("updating Elasticsearch")
        client.index(index = ESINDEXDAILY, id = nameFile, document = dicFile)
        # Actualiza tabla files
        print("updating database")
        cursor.execute("UPDATE files SET file_state= 'TRANSFORMADO'\
                            WHERE file_name = ?", (nameFile,))
        mariaDatabase.commit()
        # Manda mensaje al siguiente componente
        msg = "{\"data\": [ {\"msg\":\"" + fileName + "\", \"hostname\": \"" + HOSTNAME + "\"}]}"
        channel.basic_publish(exchange = '', routing_key = OUTPUT_QUEUE, body = msg)
        print("Message published: " + msg)
    else:
        print("File with id %s missing in Elasticsearch index %s" %(nameFile, ESINDEXDAILY))
    print("-----------------------------------------------------------------")



# Environment variables
HOSTNAME = os.getenv('HOSTNAME')
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD = os.getenv('RABBITPASS')
MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')
INPUT_QUEUE = os.getenv('INPUT_QUEUE')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
ESINDEXDAILY = os.getenv('ESINDEXDAILY')

# Conexion al servicio de la base de datos Mariadb
try:
    print("Establishing connection with MariaDB")
    mariaDatabase = mariadb.connect(
        host=MARIAHOST,
        port=int(MARIAPORT),
        user=MARIAUSER, 
        password=MARIAPASS,
        database=MARIADB
    )
    cursor = mariaDatabase.cursor()
except Error as e:
    print("Error en la conexion a la base de datos: ", e)

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

