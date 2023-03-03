import requests
import mariadb
import os
import pika
import hashlib
import json
from elasticsearch import Elasticsearch

url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"

#Enviroment Variables
hostname = os.getenv('HOSTNAME')
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITPASS')
OUTPUT_QUEUE=os.getenv('OUTPUT_QUEUE')
INPUT_QUEUE=os.getenv('INPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')

#Connection with elasticsearch
clientES = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)

#Función para recibir el msj
def callback(ch, method, properties, body):
    print('Recibiendo msj de cola.')
    json_object = json.loads(body)
    filename= json_object['data'][0]['msg']
    print(filename)
    urlFile= url + filename
    checkmd5(urlFile,filename)
    msg = "{\"data\": [ {\"msg\":\"" + filename + "\", \"hostname\": \"" + hostname + "\"}]}"
    channel_output.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=json.dumps(msg))

#Función para añadir documentos al índice file y crearlo sí no existe.
def addFileElastic(fileName,fileData):
    if not clientES.exists('files'):
        mappings = {
            "properties": {
                'filename': {"type": "text", "analyzer": "english"},
                'contents': {"type": "text", "analyzer": "english"}
            }
        }   
        clientES.indices.create(index="files", mappings=mappings)

    doc = {
        'filename': fileName,
        'contents': fileData,
    }
    clientES.index(index='files', id=fileName, document=doc)

#Función para comparar el md5 del archivo descargado al de la base de datos.
def checkmd5(urlFile,filename):
    print('Revisando md5..')
    hitFile = 1
    requestFile = requests.get(urlFile)
    requestFileData = str(requestFile.content)
    md5File = hashlib.md5(requestFileData.encode())

    # Database connection 
    MARIAHOST = os.getenv('MARIAHOST')
    MARIAPORT = os.getenv('MARIAPORT')
    MARIAUSER = os.getenv('MARIAUSER')
    MARIAPASS = os.getenv('MARIAPASS')
    MARIADB = os.getenv('MARIADB')

    # Conexion al servicio de la base de datos Mariadb
    mariaDatabase = mariadb.connect(
        host=MARIAHOST,
        port=int(MARIAPORT),
        user=MARIAUSER, 
        password=MARIAPASS,
        database=MARIADB
    )

    connection = mariaDatabase.cursor()

    connection.execute("SELECT file_md5 from files WHERE file_md5 = ?", (str(md5File.hexdigest()),))
    
    #Verificar si el md5 es diferente o igual.
    for i in connection:
        hitFile=0
        
    if hitFile:
        connection.execute('UPDATE files SET file_state = ? WHERE file_md5 = ?', ('PROCESADO', str(md5File.hexdigest()),))
        print('Procesado')
    else:
        print("Indexando en Elasticsearch..")
        addFileElastic(filename,requestFileData)
        connection.execute('UPDATE files SET file_state = ? WHERE file_name= ?', ('DESCARGADO', filename),)
        connection.execute('UPDATE files SET file_md5 = ?', (str(md5File.hexdigest())),'WHERE file_name= ?', (filename),)
        hitFile=1
    
    # Close connection
    mariaDatabase.commit()
    mariaDatabase.close()

    return    


#Conexiones para la cola.
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


print('Esperando cola..')
channel_input.start_consuming()
