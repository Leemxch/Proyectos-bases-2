import os
import re
import hashlib
import datetime
import requests
import mariadb
import unittest

class Test(unittest.TestCase):
    def test1(self):
        # Database connection 
        MARIAHOST = "localhost"
        MARIAPORT = 3306
        MARIAUSER = "root"
        MARIAPASS = "Proyecto_opcional"
        MARIADB = "weather"
        print("Establishing connection with MariaDB")
        try:
            mariaDatabase = mariadb.connect(
                host=MARIAHOST,
                port=int(MARIAPORT),
                user=MARIAUSER, 
                password=MARIAPASS,
                database=MARIADB
            )
            cursor = mariaDatabase.cursor()
        except:
            pass
        ESENDPOINT = os.getenv('ESENDPOINT')
        ESPASSWORD = os.getenv('ESPASSWORD')
        ESINDEXDAILY = "daily"
        nameFile = "AEM00041217.dly"
        try:
            client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)
        except:
            pass
        dicFile = {
                    "fileName" : "AEM00041217.dly",
                    "data": [
                        {
                            "id": "AEM00041217",
                            "date": "01011983",
                            "element": "TMAX",
                            "value": "298",
                            "mflag": "B",
                            "qflag": "M",
                            "sflag": "A"
                        }
                    ]}
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
        try:
            client.index(index = ESINDEXDAILY, id = nameFile, document = dicFile)
        except:
            pass
        # Actualiza tabla files
        print("updating database")
        try:
            cursor.execute("UPDATE files SET file_state= 'TRANSFORMADO'\
                                WHERE file_name = ?", (nameFile,))
            mariaDatabase.commit()
            mariaDatabase.close()
        except:
            pass


if __name__ == '__main__':
    unittest.main()              