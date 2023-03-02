import os
import mariadb
import pika
import json
from elasticsearch import Elasticsearch


# Busqueda en elasticsearch, devuelve el id de elasticsearch.
def elasticsearch(message):
    station_e_id = client.search(
        index="daily",
        body={
            "query": {
                "bool": {
                    "must": {
                        "match_phrase": {
                            "station_id": message,
                        }
                    },
                },
            },
        }, filter_path=['hits.hits._id']
    )
    return station_e_id


# Actualiza el mapping dentro del indice.
def elasticupdate():
    oldmapping = client.indices.get_mapping(index='daily')
    mapping = {
        "properties": {
            "station_id": {"type": "text"},
            "date": {"type": "text"},
            "month": {"type": "text"},
            "year": {"type": "text"},
            "type": {"type": "text"},
            "value": {"type": "text"},
            "nflag": {"type": "text"},
            "qflag": {"type": "text"},
            "FIPS_country_code": {"type": "text"},
            "network_code": {"type": "text"},
            "real_station_id": {"type": "text"},
            "type_name": {"type": "text"},
            "latitude": {"type": "text"},
            "longitude": {"type": "text"},
            "elevation": {"type": "text"},
            "state": {"type": "text"},
            "name": {"type": "text"},
            "gsn_flag": {"type": "text"},
            "hcn_flag": {"type": "text"},
            "wmo_id": {"type": "text"},
        }
    }
    if oldmapping != mapping:
        client.indices.put_mapping(body=mapping, index='daily')


# Environment variables
hostname = os.getenv('HOSTNAME')
RABBIT_MQ = os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD = os.getenv('RABBITPASS')
INPUT_QUEUE = os.getenv('INPUT_QUEUE')
OUTPUT_QUEUE = os.getenv('OUTPUT_QUEUE')
ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')
ESINDEXDAILY = os.getenv('ESINDEXDAILY')

# Elasticsearch connection
client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth=("elastic", ESPASSWORD), verify_certs=False)


# Función para recibir el msj
def callback(ch, method, properties, body):
    json_object = json.loads(body)
    station_id = str(json_object['msg'])
    station_id.replace('.dly', '')
    esearch = elasticsearch(station_id)
    if esearch is not None:
        elasticupdate()

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

        # Traer datos de la base.
        connection.execute(
            "SELECT latitude, longitude, elevation, state, name, gsn_flag, hcn_flag, wmo_id FROM files WHERE file_name=?",
            (station_id,))
        records = connection.fetchall()

        # Pasar los datos de la base a un body que actualizara el record en Elasticsearch.
        for row in records:
            body = {
                "doc": {
                    "latitude": row[0],
                    "longitude": row[1],
                    "elevation": row[2],
                    "state": row[3],
                    "name": row[4],
                    "gsn_flag": row[5],
                    "hcn_flag": row[6],
                    "wmo_id": row[7]
                }
            }

        station_e_id = elasticsearch(station_id)
        client.update(index='daily', id=station_e_id, body=body)
        connection.execute("UPDATE files SET file_state='CON_ESTACION' WHERE file_name=?", (station_id,))

        result = station_id

        msg = "{\"data\": [ {\"msg\":\"" + result + "\", \"hostname\": \"" + hostname + "\"}]}"
        channel_output.basic_publish(exchange='', routing_key=OUTPUT_QUEUE, body=msg)

        connection.close()
        mariaDatabase.commit()
        mariaDatabase.close()


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

print('Esperando cola..')

channel_input.start_consuming()
