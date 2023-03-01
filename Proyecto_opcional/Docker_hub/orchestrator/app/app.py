import time
import os
import requests
import pika
from bs4 import BeautifulSoup
import sys
from datetime import datetime
import hashlib
import json
import mariadb

hostname = os.getenv('HOSTNAME')
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD = os.getenv('RABBITPASS')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE')


def arrangeFiles(list):
    newList = []
    fileCount = 0
    maxFiles = 5000
    for file in list:
        fileCount = fileCount + 1
        if file.text.find('.dly') != -1:
            newList = newList + [file.text]
            # with open('test.txt', 'a') as f:
            # f.write(file.text + '  ')
        if fileCount == maxFiles:
            return newList
    return newList


print("Trayendo archivos...")
url = ("https://www.ncei.noaa.gov/pub/data/ghcn/daily/all");
requestFiles = requests.get(url)
filesSoup = BeautifulSoup(requestFiles.text, 'html.parser')
files = filesSoup.findAll('a')
files = arrangeFiles(files)
files.pop(0)

print("Conectando a la base de datos...")

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

'''
mariaDatabase = mariadb.connect(
    host="localhost",
    port=3306,
    user="root",
    password="gmlsdrhn2",
    database="weather"
)
'''
print("Creando Cursor...")
connection = mariaDatabase.cursor()

print("Corriendo Query...")

for file in files:
    hitFile = 1
    urlFile = url + '/' + file
    connection.execute("SELECT file_name from files WHERE file_name=?", (file,))
    if connection.rowcount != 0 and connection.rowcount != -1:
        for i in connection:
            connection.execute("UPDATE files SET file_date=now() WHERE file_name=?", (file,))
            hitFile = 0
        if hitFile:
            connection.execute(
                "INSERT INTO files(file_name, file_url, file_date, file_state, file_md5) VALUES(?, ?, now(), 'LISTADO', 'null')",
                (file, urlFile))
            hitFile = 1

connection.close()
mariaDatabase.commit()
mariaDatabase.close()

credentials = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue=OUTPUT_QUEUE)

for file in files:
    result = file
    msg = "{\"data\": [ {\"msg\":\"" + result + "\", \"hostname\": \"" + hostname + "\"}]}"
    channel.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=msg)


