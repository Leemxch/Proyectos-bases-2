import os
import mariadb
import pika
import json
from elasticsearch import Elasticsearch

# Environment variables
hostname = os.getenv('HOSTNAME')
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD = os.getenv('RABBITPASS')
INPUT_QUEUE = os.getenv('INPUT_QUEUE')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
ESINDEXDAILY = os.getenv('ESINDEXDAILY')

MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth=("elastic", ESPASSWORD), verify_certs=False)


# Función para recibir el msj
def callback(ch, method, properties, body):
    message = json.loads(body)
    print("Message received: ")
    print(message)
    fileName = message['data'][0]['msg']
    nameFile = fileName[0:len(fileName)]
    station_id = nameFile.replace('.dly', '')
    dataFile = client.get(index=ESINDEXDAILY, id=nameFile)
    # si existe
    if dataFile['found']:
        print("Found file in Elasticsearch: " + str(nameFile) + ".")
        dicFile = dataFile['_source']
        dicDataList = dicFile['data']

        # Conexion al servicio de la base de datos Mariadb
        print("Establishing connection with MariaDB...")
        mariaDatabase = mariadb.connect(
            host=MARIAHOST,
            port=int(MARIAPORT),
            user=MARIAUSER,
            password=MARIAPASS,
            database=MARIADB
        )
        connection = mariaDatabase.cursor()

        print("Obtaining station where station_id = " + station_id)
        connection.execute(
            "SELECT * FROM stations WHERE station_id = ?",
            (station_id,))

        print("Adding values...")
        # trae valores de la base de datos
        for j in range(0, len(dicDataList)):
            for i in connection:
                print('EXISTE RECORD')
                # agrega valores del station_id
                dicDataList[j]['latitude'] = str(i[1])
                dicDataList[j]['longitude'] = str(i[2])
                dicDataList[j]['elevation'] = str(i[3])
                dicDataList[j]['state'] = str(i[4])
                dicDataList[j]['name'] = str(i[5])
                dicDataList[j]['gsn_flag'] = str(i[6])
                dicDataList[j]['hcn_flag'] = str(i[7])
                dicDataList[j]['wmo_id'] = str(i[8])

        dicFile['data'] = dicDataList
        # Actualiza datos en Elasticsearch
        print("Updating Elasticsearch...")
        client.index(index=ESINDEXDAILY, id=nameFile, document=dicFile)

        # Actualiza datos en MariaDB
        print("Updating file_state in MariaDB...")
        connection.execute("UPDATE files SET file_state='CON_ESTACION' WHERE file_name=?", (nameFile,))
        result = nameFile

        print("Enviando mensaje con RabbitMQ...")
        msg = "{\"data\": [ {\"msg\":\"" + result + "\", \"hostname\": \"" + hostname + "\"}]}"
        channel_output.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=msg)

        connection.close()
        mariaDatabase.commit()
        mariaDatabase.close()
    else:
        print("File with id %s missing in Elasticsearch index %s" % (nameFile, ESINDEXDAILY))
    print("-----------------------------------------------------------------")


# RabbitMQ connection
credentials_input = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_input = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_input)
connection_input = pika.BlockingConnection(parameters_input)
channel_input = connection_input.channel()
channel_input.queue_declare(queue=INPUT_QUEUE)
channel_input.basic_consume(queue=INPUT_QUEUE, on_message_callback=callback, auto_ack=True)

credentials_output = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_output = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_output)
connection_output = pika.BlockingConnection(parameters_output)
channel_output = connection_output.channel()
channel_output.queue_declare(queue=OUTPUT_QUEUE)

print('Esperando cola...')

channel_input.start_consuming()
