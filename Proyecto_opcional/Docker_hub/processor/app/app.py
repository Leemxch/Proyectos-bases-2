import requests
import mariadb
import os
import pika
import hashlib
import json

url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all"

hostname = os.getenv('HOSTNAME')
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITPASS')
OUTPUT_QUEUE=os.getenv('OUTPUT_QUEUE')
INPUT_QUEUE=os.getenv('INPUT_QUEUE')


def callback(ch, method, properties, body):
    json_object = json.loads(body)
    filename= json_object.getString('message')
    urlFile= url + filename
    checkmd5(urlFile,filename)
    #channel_output.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=json.dumps(json_object))
    print(json_object)

def checkmd5(urlFile,filename):
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
    
    for i in connection:
        hitFile=0
         
    if hitFile:
        connection.execute('UPDATE files SET file_state=PROCESADO WHERE file_md5 = ?', (str(md5File.hexdigest()),))
    else:
        print("Found change in file")
        ##Almacenar en ElasticSearch en indice files.
        connection.execute('UPDATE files SET file_state=DESCARGADO WHERE file_name= ?', (filename),)
        connection.execute('UPDATE files SET file_md5=?', (str(md5File.hexdigest())),'WHERE file_name= ?', (filename),)
        hitFile=1

    return


credentials_input = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_input = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_input)
connection_input = pika.BlockingConnection(parameters_input)
channel_input = connection_input.channel()
channel_input.queue_declare(queue=INPUT_QUEUE)
channel_input.basic_consume(queue=INPUT_QUEUE, on_message_callback=callback, auto_ack=True) 


'''
credentials_output = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_output = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_output)
connection_output = pika.BlockingConnection(parameters_output)
channel_output = connection_output.channel()
channel_output.queue_declare(queue=OUTPUT_QUEUE)
'''

channel_input.start_consuming()
