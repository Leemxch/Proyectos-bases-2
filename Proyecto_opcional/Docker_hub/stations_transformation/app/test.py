import requests
import mariadb
import os
import hashlib
from elasticsearch import Elasticsearch
import unittest

class test(unittest.TestCase):
    def test1(self):
        # Elasticsearch connection
        print("Test to transform data related to stations for files.")
        ESENDPOINT = os.getenv('ESENDPOINT')
        ESPASSWORD = os.getenv('ESPASSWORD')
        ESINDEXDAILY = 'daily'

        try:
            client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth=("elastic", ESPASSWORD), verify_certs=False)
        except:
            pass

        url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/"
        fileName = 'ACW00011604.dly'

        #Added code for our test to work
        urlFile = url + fileName
        nameFile = fileName[0:len(fileName)]
        station_id = nameFile.replace('.dly', '')
        requestFile = requests.get(urlFile)
        fileData = str(requestFile.content)
        doc = {
            'filename': fileName,
            'contents': fileData,
        }
        try:
            client.indices.create(index=ESINDEXDAILY, mappings=doc)
        except:
            pass

        try:
            dataFile = client.get(index=ESINDEXDAILY, id=nameFile)
        except:
            pass

        # si existe
        try:
            if dataFile['found']:
                print("Found file in Elasticsearch: " + str(nameFile) + ".")
                dicFile = dataFile['_source']
                dicDataList = dicFile['data']

                # Conexion al servicio de la base de datos Mariadb
                print("Establishing connection with MariaDB...")
                mariaDatabase = mariadb.connect(
                    host="localhost",
                    port=int('3306'),
                    user="root",
                    password="gmlsdrhn2",
                    database="weather"
                )
                connection = mariaDatabase.cursor()

                connection.execute("CREATE TABLE IF NOT EXISTS stations(\
                                    station_id varchar(16) not null,\
                                    latitude float,\
                                    longitude float,\
                                    elevation float,\
                                    state varchar(4) not null,\
                                    name varchar(64) not null,\
                                    gsn_flag varchar(4) not null,\
                                    hcn_flag varchar(4) not null,\
                                    wmo_id varchar(8) not null,\
                                    country_id int,\
                                    state_id int,\
                                    primary key(station_id),\
                                    foreign key (country_id) references countries (country_id),\
                                    foreign key (state_id) references states (state_id)\
                    )")

                connection.execute("INSERT INTO stations(station_id, state, name, gsn_flag, hcn_flag, wmo_id) VALUES(\
                ?, ?, now(), 'LISTADO', 'null')", (station_id, 'mstate', 'mname', 'mgsn', 'mhcn', 'wmo'))

                print("Adding values...")
                # trae valores de la base de datos
                for j in range(0, len(dicDataList)):
                    print("Obtaining station where station_id = " + station_id)
                    connection.execute("SELECT * FROM stations WHERE station_id = ?", (station_id,))
                    for i in connection:
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
                result = fileName

                mariaDatabase.commit()
                mariaDatabase.close()
        except:
            pass
        print("End of: Test to transform data related to stations for files.")


if __name__ == '__main__':
    unittest.main()

